#!/usr/bin/env bash
# Installe et lance tout le projet. Une seule commande apres un clone.
#
#   ./demarrer.sh              installe, construit les modeles, ouvre les interfaces
#   ./demarrer.sh --rapide     saute dbt, pour repartir vite quand tout est deja en place
#   ./demarrer.sh --complet    lance aussi l'ingestion avant dbt
#
# Airflow    http://localhost:8080
# dbt docs   http://localhost:8081
# Dashboard  http://localhost:8501
#
# Le script est idempotent : relance-le autant de fois que tu veux, il ne
# reinstalle que ce qui manque. Ctrl+C arrete les trois services d'un coup.

set -euo pipefail
cd "$(dirname "$0")"
RACINE="$PWD"

PYTHON="${PYTHON:-python3.12}"
MODE="${1:-}"

# Airflow, dbt et Streamlit ne peuvent pas partager un venv : leurs versions de
# google-cloud-* sont incompatibles. D'ou trois environnements.
VENV="$RACINE/venv"
VENV_AIRFLOW="$RACINE/venv-airflow"
VENV_DASHBOARD="$RACINE/venv-dashboard"

CONTRAINTES="https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt"
JOURNAUX="$RACINE/logs"

titre() { printf '\n\033[1m%s\033[0m\n' "$1"; }
info()  { printf '  %s\n' "$1"; }
echec() { printf '\n\033[31mArret : %s\033[0m\n\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- verifications

command -v "$PYTHON" >/dev/null \
  || echec "$PYTHON introuvable. Installe Python 3.12, ou passe PYTHON=python3.13 ./demarrer.sh"

# La cle de service n'est pas dans le depot, et ne doit pas y etre. Sans elle,
# rien ne peut lire BigQuery : autant le dire tout de suite plutot que d'echouer
# dix minutes plus tard, apres l'installation d'Airflow.
CLE="${MBDA_KEYFILE:-$HOME/.gcp/mbda-projet2-sa.json}"
if [ ! -f "$CLE" ]; then
  echec "cle de service absente.

  Attendue ici : $CLE
  Ou ailleurs  : MBDA_KEYFILE=/chemin/vers/cle.json ./demarrer.sh

  Elle se transmet de la main a la main, jamais par le depot."
fi
export MBDA_KEYFILE="$CLE"

# Le dashboard a son propre compte, en lecture seule. S'il manque, la cle
# principale fait l'affaire : elle peut tout lire.
CLE_DASHBOARD="${MBDA_DASHBOARD_KEYFILE:-$HOME/.gcp/mbda-dashboard-ro.json}"
[ -f "$CLE_DASHBOARD" ] || CLE_DASHBOARD="$CLE"
export MBDA_DASHBOARD_KEYFILE="$CLE_DASHBOARD"

# ---------------------------------------------------------------- installation

installer() {
  local chemin="$1" fichier="$2" temoin="$3" nom="$4"
  shift 4
  if [ -x "$chemin/bin/$temoin" ]; then
    info "$nom : deja en place"
    return
  fi
  info "$nom : installation, cela peut prendre quelques minutes"
  [ -d "$chemin" ] || "$PYTHON" -m venv "$chemin"
  "$chemin/bin/pip" install --quiet --upgrade pip

  # dbt-core tire dbt-core-experimental-parser, dont le build telecharge un
  # binaire depuis GitHub. Ce telechargement coupe parfois, il a fait tomber le
  # pipeline le 12 aout. Meme reprise que dans .github/workflows/pipeline.yml.
  local essai
  for essai in 1 2 3; do
    if "$chemin/bin/pip" install --quiet -r "$fichier" "$@"; then
      return
    fi
    info "$nom : echec, tentative $essai sur 3"
    sleep 15
  done
  echec "installation impossible ($nom). Verifie la connexion, puis relance."
}

titre "Environnements"
installer "$VENV"           requirements.txt           dbt       "ingestion et dbt"
installer "$VENV_DASHBOARD" requirements-dashboard.txt streamlit "tableau de bord"
installer "$VENV_AIRFLOW"   requirements-airflow.txt   airflow   "Airflow" -c "$CONTRAINTES"

# ------------------------------------------------------------- setproctitle
#
# Sur macOS, setproctitle (dependance d'apache-airflow, utilisee par gunicorn
# et par plusieurs modules Airflow pour renommer les process) appelle des
# fonctions CoreFoundation/os_log juste apres fork(), avant exec(). macOS ne
# supporte pas cet appel dans un process multi-thread : chaque worker
# segfaultait aussitot et gunicorn en relancait un autre en boucle. Le 18
# aout, plus de 12 000 crashes en quelques secondes. Airflow importe
# setproctitle directement a plusieurs endroits (dag_processing/manager.py,
# executors/local_executor.py, etc.) sans try/except : le desinstaller casse
# ces imports. On le remplace donc par un stub qui offre la meme API sans
# toucher au titre du process. Linux n'est pas concerne, setproctitle y
# fonctionne normalement : on ne touche a rien hors macOS.
if [ "$(uname -s)" = "Darwin" ]; then
  if ! "$VENV_AIRFLOW/bin/python" -c "
import setproctitle, sys
sys.exit(0 if getattr(setproctitle, '__version__', '') == '0.0.0-stub' else 1)
" 2>/dev/null; then
    info "setproctitle : remplacement par un stub (bug fork-safety macOS, cf commentaire)"
    SITE_AIRFLOW="$("$VENV_AIRFLOW/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
    rm -rf "$SITE_AIRFLOW/setproctitle" "$SITE_AIRFLOW"/setproctitle-*.dist-info
    mkdir -p "$SITE_AIRFLOW/setproctitle"
    cat > "$SITE_AIRFLOW/setproctitle/__init__.py" <<'PYEOF'
"""Stub sans effet, a la place du paquet setproctitle natif.

Le vrai paquet appelle CoreFoundation/os_log juste apres fork(), avant
exec(), ce qui segfault sur macOS recent (process multi-thread, appel non
fork-safe). Voir le commentaire dans demarrer.sh.
"""

__version__ = "0.0.0-stub"


def setproctitle(title):
    pass


def getproctitle():
    return "python"


def setthreadtitle(title):
    pass


def getthreadtitle():
    return ""
PYEOF
  fi
fi

# ---------------------------------------------------------------- profil dbt

# Genere dans le projet, pas dans ~/.dbt : on ne touche pas au profil personnel
# de celui qui clone, qui a peut-etre deja ses propres cibles.
export DBT_PROFILES_DIR="$RACINE/.dbt"
mkdir -p "$DBT_PROFILES_DIR"
cat > "$DBT_PROFILES_DIR/profiles.yml" <<EOF
dbt_pipeline:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: crucial-bonsai-418120
      dataset: marts
      keyfile: $CLE
      threads: 4
      location: EU
EOF

# ---------------------------------------------------------------- pipeline

mkdir -p "$JOURNAUX"

if [ "$MODE" = "--complet" ]; then
  titre "Ingestion"
  info "collecte des trois sources, environ 90 secondes"
  "$VENV/bin/python" scripts/ingest.py
fi

if [ "$MODE" != "--rapide" ]; then
  titre "Modeles dbt"
  cd "$RACINE/dbt_pipeline"
  "$VENV/bin/dbt" deps --quiet
  "$VENV/bin/dbt" seed --quiet
  "$VENV/bin/dbt" run --quiet
  "$VENV/bin/dbt" test --quiet
  "$VENV/bin/dbt" docs generate --quiet
  cd "$RACINE"
  info "modeles construits et testes"
elif [ ! -f "$RACINE/dbt_pipeline/target/catalog.json" ]; then
  echec "--rapide demande une documentation dbt deja generee. Lance ./demarrer.sh une fois sans l'option."
fi

# ---------------------------------------------------------------- services

export AIRFLOW_HOME="$RACINE/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$RACINE/airflow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export MBDA_SMTP_USER="${MBDA_SMTP_USER:-}"
export MBDA_SMTP_PASSWORD="${MBDA_SMTP_PASSWORD:-}"
export MBDA_SMTP_TO="${MBDA_SMTP_TO:-}"

PIDS=()
arreter() {
  printf '\n\033[1mArret des services.\033[0m\n'
  for pid in "${PIDS[@]:-}"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  exit 0
}
trap arreter INT TERM

titre "Services"

# standalone relance ses sous-processus via le PATH : pointer le binaire ne
# suffit pas.
( export PATH="$VENV_AIRFLOW/bin:$PATH"
  exec "$VENV_AIRFLOW/bin/airflow" standalone ) > "$JOURNAUX/airflow.log" 2>&1 &
PIDS+=($!)
info "Airflow demarre, journal dans logs/airflow.log"

( cd "$RACINE/dbt_pipeline"
  exec "$VENV/bin/dbt" docs serve --port 8081 --no-browser ) > "$JOURNAUX/dbt-docs.log" 2>&1 &
PIDS+=($!)

"$VENV_DASHBOARD/bin/streamlit" run dashboard/app.py \
  --server.port 8501 --server.headless true > "$JOURNAUX/dashboard.log" 2>&1 &
PIDS+=($!)

# Airflow met une vingtaine de secondes a ecrire son mot de passe.
MDP="$AIRFLOW_HOME/standalone_admin_password.txt"
for _ in $(seq 1 40); do [ -f "$MDP" ] && break; sleep 1; done

# Le DAG reste en pause, volontairement. Sortir un DAG de pause ne fait pas
# que le rendre declenchable : l'ordonnanceur rattrape aussitot les executions
# en attente. Le 2026-08-15, un run planifie du 13 aout, herite de l'epoque ou
# le DAG avait un calendrier, est reparti tout seul et a reecrit les tables
# raw sans que personne ne l'ait demande.
#
# Pour le lancer, l'interrupteur est en haut a gauche dans l'interface, puis
# le bouton de declenchement. Un geste, et il est conscient.

# Purge de securite : un DagRun de cette meme epoque peut encore trainer en
# base, pret a repartir des qu'un humain depausera le DAG depuis l'interface.
# La pause n'empeche que l'ordonnancement, pas l'execution d'un run deja en
# file. On neutralise donc tout run non termine a chaque demarrage, qu'il y
# en ait un ou pas.
( export PATH="$VENV_AIRFLOW/bin:$PATH"
  "$VENV_AIRFLOW/bin/python" - <<'PY'
from airflow.models import DagRun, TaskInstance
from airflow.utils.session import create_session
from airflow.utils.state import DagRunState, TaskInstanceState

DAG_ID = "ingest_market_data"

with create_session() as session:
    runs = [
        run_id
        for (run_id,) in session.query(DagRun.run_id)
        .filter(DagRun.dag_id == DAG_ID)
        .filter(DagRun.state.in_([DagRunState.QUEUED, DagRunState.RUNNING]))
        .all()
    ]
    if runs:
        session.query(TaskInstance).filter(
            TaskInstance.dag_id == DAG_ID, TaskInstance.run_id.in_(runs)
        ).update({TaskInstance.state: TaskInstanceState.FAILED}, synchronize_session=False)
        session.query(DagRun).filter(
            DagRun.dag_id == DAG_ID, DagRun.run_id.in_(runs)
        ).update({DagRun.state: DagRunState.FAILED}, synchronize_session=False)
        session.commit()
        print(f"{len(runs)} DagRun(s) residuel(s) neutralise(s) : {', '.join(runs)}")
PY
) >> "$JOURNAUX/airflow.log" 2>&1 || true

cat <<EOF

  Airflow     http://localhost:8080     admin / $( [ -f "$MDP" ] && cat "$MDP" || echo "voir $MDP" )
  dbt docs    http://localhost:8081
  Dashboard   http://localhost:8501

  Ctrl+C pour tout arreter.

EOF

wait
