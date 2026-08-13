# Captures d'écran du rapport

Un fichier par capture, numéroté dans l'ordre où il apparaît dans le rapport.
Le numéro ne change jamais, même si une capture est refaite : on écrase le
fichier, on ne le renomme pas. Les renvois du rapport restent ainsi valables.

**Format** : PNG, largeur 1400 px minimum, thème clair. Éviter les captures de
plein écran où le contenu utile occupe un quart de l'image, recadrer sur la zone
qui compte.

**Avant de capturer quoi que ce soit dans BigQuery ou Airflow**, lancer le
pipeline pour que les données soient fraîches et les tables présentes :

```bash
export AIRFLOW_HOME=$PWD/airflow_home
export AIRFLOW__CORE__DAGS_FOLDER=$PWD/airflow/dags
export PATH=/chemin/vers/venv-airflow/bin:$PATH
airflow dags test ingest_market_data
```

---

## Déjà dans le dépôt, rien à faire

| Fichier | Source | Section du rapport |
|---|---|---|
| `01-architecture.png` | `docs/img/architecture.png` | Architecture technique |
| `02-datasets.png` | `docs/img/datasets.png` | Les trois datasets |
| `04-schema-etoile.png` | `docs/img/schema_etoile.png` | Modèle dimensionnel |

Ces trois images sont générées par `python docs/diagramme/rendre.py` et
`python docs/diagramme/frames.py`. Les régénérer si le modèle change.

---

## À prendre dans BigQuery

**`03-bigquery-datasets.png`** — Console BigQuery, panneau de gauche déplié sur le
projet `crucial-bonsai-418120`, montrant les trois datasets `raw`,
`marts_staging` et `marts` avec leurs tables. Dérouler les trois.
*Prouve que l'architecture décrite existe réellement.*

**`05-bigquery-marts.png`** — Onglet *Détails* de `marts.fct_cotation_journaliere`.
Doit montrer le nombre de lignes (103 104), la taille, et surtout le champ
**Clustering** avec `instrument_id, date_cotation`, et l'absence de partitionnement.
*Appuie le paragraphe sur les contraintes du Sandbox.*

**`19-bigquery-schema.png`** — Onglet *Schéma* de la même table, avec les
13 colonnes dont `variation_exploitable`.
*Utile si le rapport détaille la table de faits.*

---

## À prendre dans dbt

**`06-dbt-build.png`** — Terminal après `dbt build`, cadré sur les dernières
lignes : `Completed successfully` et `PASS=87 WARN=0 ERROR=0`.
*Preuve que les 68 tests passent.*

**`07-dbt-docs-lineage.png`** — Graphe de dépendances. Le générer puis le servir :

```bash
cd dbt_pipeline && ../venv/bin/dbt docs generate && ../venv/bin/dbt docs serve
```

Ouvrir `http://localhost:8080`, cliquer sur l'icône en bas à droite pour le
*lineage graph*, et cadrer sur l'enchaînement sources → staging → marts →
analytique.
*C'est la plus parlante du dossier : elle montre les 17 modèles et leurs liens.*

---

## À prendre dans Airflow

Lancer l'interface avec `./lancer_airflow.sh`, puis `http://localhost:8080`.

**`08-airflow-graphe.png`** — Vue *Graph* du DAG `ingest_market_data`, groupes
`marches`, `referentiels` et `transformation` **dépliés**, les 16 tâches visibles.
*Illustre la section orchestration.*

**`09-airflow-succes.png`** — Vue *Grid* après une exécution complète, toutes les
cases en vert, avec la durée totale affichée.
*Preuve que le pipeline tourne de bout en bout.*

**`20-airflow-logs-recapituler.png`** — Log de la tâche `recapituler`, qui liste
les 11 tables de `marts` avec leur nombre de lignes.
*Chiffres vérifiables d'un coup d'œil.*

---

## À prendre sur GitHub

**`10-github-actions.png`** — Onglet *Actions*, exécution du workflow
« Pipeline quotidien » dépliée, les 8 étapes en vert.
*Montre l'ordonnancement autonome.*

**`11-alerte-mail.png`** — Le courriel d'alerte reçu après un échec. Si aucun
échec récent, le provoquer volontairement : dupliquer le DAG avec `retries: 0` et
faire échouer une tâche, sinon l'alerte n'est envoyée qu'après trois relances
espacées de 5 minutes. **Masquer l'adresse de destination** avant d'insérer
l'image dans le rapport.
*Illustre la supervision.*

**`21-github-pr.png`** — La liste des pull requests fermées, montrant les revues
croisées entre les membres.
*Appuie la section sur l'organisation du travail.*

---

## À prendre dans le tableau de bord

Cinq captures, une par question métier, prises dans l'application Streamlit.

| Fichier | Page |
|---|---|
| `12-dashboard-q1.png` | Régime de change et volatilité |
| `13-dashboard-q2.png` | Volatilité par classe d'actif |
| `14-dashboard-q3.png` | Exposition des exportations |
| `15-dashboard-q4.png` | Corrélations société / matière |
| `16-dashboard-q5.png` | Périodes de tension |

Cadrer sur la page entière, bandeau de titre compris, pour qu'on voie la phrase
de réponse sous chaque titre.

---

## Les preuves des deux incidents

Ces deux captures servent la partie la plus intéressante du rapport. Elles se
prennent dans la console BigQuery, onglet résultats.

**`17-wti-negatif.png`** — Résultat de cette requête :

```sql
select date_cotation, instrument_id, cloture, variation_pct, variation_exploitable
from `crucial-bonsai-418120`.marts.fct_cotation_journaliere
where instrument_id = 'CL=F'
  and date_cotation between '2020-04-17' and '2020-04-22'
order by date_cotation
```

*On voit la clôture à -37,63 et la variation à -305,97 %.*

**`18-yahoo-longname.png`** — Sortie du terminal prouvant que `GOLD` n'est pas
Barrick :

```bash
python - <<'PY'
import requests
E = {"User-Agent": "Mozilla/5.0"}
for t in ["GOLD", "B"]:
    r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}",
                     headers=E, params={"range": "5d", "interval": "1d"}, timeout=30)
    m = r.json()["chart"]["result"][0]["meta"]
    print(t, "->", m.get("longName"))
PY
```

*Affiche `GOLD -> Gold.com, Inc.` et `B -> Barrick Mining Corporation`.*

**`22-correlation-barrick.png`** — Optionnelle mais très parlante :

```sql
select annee, correlation
from `crucial-bonsai-418120`.marts.agg_correlation_paire_annee
where paire_id = 'barrick_or' order by annee
```

*Montre la stabilité retrouvée après correction du ticker.*

---

## Ce qui est dans le dossier

| Fichier | Contenu | Origine |
|---|---|---|
| `01-architecture.png` | la chaîne de bout en bout | généré par `rendre.py` |
| `architecture.png` | la même, en 3420 × 840 | export manuel |
| `architecture_poster.png` | la même, en 4080 × 2300 | export manuel |
| `pipeline.gif` | la chaîne animée | export manuel |
| `02-datasets.png` | les trois datasets BigQuery | généré par `rendre.py` |
| `04-schema-etoile.png` | le modèle dimensionnel | généré par `rendre.py` |
| `dag_airflow.png` | le DAG, 16 tâches en vert | capture Airflow |
| `dbt-dag.png` | le lineage dbt complet | capture dbt docs |

Les trois versions de l'architecture font double emploi. Garder celle qui rend
le mieux à l'impression et retirer les autres avant de rendre.

## Ce qui manque encore

| # | Capture | Où la prendre |
|---|---|---|
| 03 | les trois datasets dans la console | BigQuery, panneau de gauche déplié |
| 05 | détails de `fct_cotation_journaliere` | BigQuery, onglet Détails, montrer le clustering |
| 06 | `dbt build` en succès | terminal, cadré sur `PASS=87` |
| 09 | vue Grid d'une exécution | Airflow, tout en vert, durée affichée |
| 10 | le workflow en succès | GitHub, onglet Actions |
| 11 | le courriel d'alerte | boîte mail, **masquer l'adresse** |
| 12-16 | les cinq pages du tableau de bord | l'application Streamlit |
| 17 | le WTI à prix négatif | BigQuery, requête donnée plus haut |
| 18 | `longName` du ticker | terminal, script donné plus haut |
