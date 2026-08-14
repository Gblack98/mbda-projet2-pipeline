# Pipeline analytics — matières premières et devises

Collecte quotidienne de 41 instruments financiers et de 15 devises, structurés
en schéma en étoile puis agrégés en indicateurs.

```
Yahoo Finance ┐
Frankfurter   ├─► ingestion ─► BigQuery.raw ─► dbt ─► BigQuery.marts ─► BI
Banque Mondiale ┘
```

## Sources

| Source | Données | Fréquence | Clé |
|---|---|---|---|
| Yahoo Finance | 41 instruments, OHLCV | quotidienne | non |
| Frankfurter (BCE) | 15 devises | quotidienne | non |
| Banque Mondiale | exportations par pays | annuelle | non |

## Stack

Airflow · BigQuery · dbt Core · Streamlit

## Modèle

Granularité de la table de faits : **un instrument, un jour**.

```
dim_temps ┐
dim_instrument ├─► fct_cotation_journaliere
dim_devise ┘

fct_exportations_pays (grain distinct : pays × catégorie × année, non jointe)
```

Six tables d'agrégation complètent le modèle : volatilité par classe et par
année, tension mensuelle, corrélations société / matière première, évolution
des exportations, indicateurs annuels par instrument. Les chiffres du rapport
sortent de ces tables, pas de calculs refaits dans l'outil de restitution.

![Datasets](docs/captures/02-datasets.png)

Guide du tableau de bord : [docs/guide-dashboard.md](docs/guide-dashboard.md).
Dossier de rédaction du rapport : [docs/dossier-rapport.md](docs/dossier-rapport.md).

Détails et diagrammes : [docs/architecture.md](docs/architecture.md).
Questions métier et construction du tableau de bord :
[docs/questions-metier.md](docs/questions-metier.md).

## Exécution

Le workflow GitHub Actions est le seul déclencheur planifié, les jours ouvrés
à 18h37. Le DAG Airflow couvre le même périmètre en déclenchement manuel.
N'en planifier qu'un : ils écrivent les mêmes tables en `WRITE_TRUNCATE`.

## Lancer

Une seule commande après le clone :

```bash
./demarrer.sh
```

Elle crée les trois environnements, installe les dépendances, construit les
modèles dbt, lance les tests, puis ouvre :

| Interface | Adresse |
|---|---|
| Airflow | http://localhost:8080 |
| Documentation dbt | http://localhost:8081 |
| Tableau de bord | http://localhost:8501 |

L'identifiant Airflow est `admin`, le mot de passe s'affiche au démarrage.
`Ctrl+C` arrête les trois services.

**Il faut la clé de service BigQuery.** Elle n'est pas dans le dépôt et ne doit
pas y être. Le script l'attend dans `~/.gcp/mbda-projet2-sa.json`, ou à
l'endroit indiqué par `MBDA_KEYFILE` :

```bash
MBDA_KEYFILE=/chemin/vers/cle.json ./demarrer.sh
```

Deux variantes :

```bash
./demarrer.sh --complet    # lance aussi l'ingestion des trois sources avant dbt
./demarrer.sh --rapide     # saute dbt, quand tout est déjà construit
```

Le script est idempotent, il ne réinstalle que ce qui manque. Trois
environnements séparés parce qu'Airflow, dbt et Streamlit exigent des versions
incompatibles de `google-cloud-*`.

Sans passer par le script :

```bash
pip install -r requirements.txt
python scripts/ingest.py          # remplit raw, puis contrôle ce qui est chargé
cd dbt_pipeline && dbt build      # construit marts et lance les tests
```
