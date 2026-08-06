#!/usr/bin/env bash
# Lance Airflow en local : interface web sur http://localhost:8080
set -e
cd "$(dirname "$0")"

export AIRFLOW_HOME="$PWD/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/airflow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# alertes mail : laisser vide desactive l'envoi sans faire echouer les taches
export MBDA_SMTP_USER="${MBDA_SMTP_USER:-}"
export MBDA_SMTP_PASSWORD="${MBDA_SMTP_PASSWORD:-}"
export MBDA_SMTP_TO="${MBDA_SMTP_TO:-}"

VENV=/home/gblack98/Téléchargements/cedeao-remitflow/venv-airflow
# standalone relance ses sous-processus via le PATH
export PATH="$VENV/bin:$PATH"
AIRFLOW="$VENV/bin/airflow"

echo "Interface   : http://localhost:8080"
echo "Identifiant : admin"
echo "Mot de passe: $AIRFLOW_HOME/standalone_admin_password.txt"
echo
exec "$AIRFLOW" standalone
