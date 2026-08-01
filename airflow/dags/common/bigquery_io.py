"""Écriture dans BigQuery — chargement idempotent par partition.

Le mode Sandbox interdit les instructions DML : impossible de faire un DELETE
puis un INSERT, ni un MERGE. L'idempotence passe donc par le décorateur de
partition : un load job visant `table$20260801` en mode WRITE_TRUNCATE
remplace intégralement la journée concernée, sans toucher aux autres.

Conséquence pratique : relancer le DAG deux fois sur la même date aboutit au
même état. C'est la propriété qui distingue un pipeline d'un script.
"""

from collections import defaultdict

from google.cloud import bigquery
from google.oauth2 import service_account

from . import config, schemas


def client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_file(config.KEYFILE)
    return bigquery.Client(project=config.PROJET, credentials=creds)


def assurer_dataset(bq: bigquery.Client, dataset: str) -> None:
    ref = bigquery.Dataset(f"{config.PROJET}.{dataset}")
    ref.location = config.LOCATION
    bq.create_dataset(ref, exists_ok=True)


def assurer_table(bq: bigquery.Client, table: str) -> str:
    """Crée la table partitionnée et clusterisée si elle n'existe pas.

    Le partitionnement conditionne l'idempotence : sans lui, on ne peut pas
    remplacer une journée isolément.
    """
    table_id = f"{config.PROJET}.{config.DATASET_RAW}.{table}"
    ref = bigquery.Table(table_id, schema=schemas.SCHEMAS[table])
    ref.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field=schemas.PARTITION[table],
    )
    ref.clustering_fields = schemas.CLUSTERING[table]
    bq.create_table(ref, exists_ok=True)
    return table_id


def _config_chargement(table: str) -> bigquery.LoadJobConfig:
    return bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=schemas.SCHEMAS[table],
    )


def charger_par_partition(bq: bigquery.Client, table: str, lignes: list) -> dict:
    """Charge les lignes en remplaçant chaque partition journalière visée.

    Les lignes sont regroupées par date, puis chaque groupe est écrit dans sa
    propre partition. Une date absente du lot n'est pas touchée.

    Renvoie {date: nombre de lignes chargées}.
    """
    if not lignes:
        return {}

    champ_date = schemas.PARTITION[table]
    table_id = assurer_table(bq, table)

    par_date = defaultdict(list)
    for ligne in lignes:
        par_date[ligne[champ_date]].append(ligne)

    charge = {}
    for jour, lot in sorted(par_date.items()):
        suffixe = jour.replace("-", "")
        travail = bq.load_table_from_json(
            lot,
            f"{table_id}${suffixe}",
            job_config=_config_chargement(table),
        )
        travail.result()  # lève une exception si le chargement échoue
        charge[jour] = len(lot)

    return charge


def charger_integralement(bq: bigquery.Client, table: str, lignes: list) -> int:
    """Remplace toute la table en une fois.

    Réservé à la reprise d'historique : écrire dix ans partition par
    partition représenterait plusieurs milliers de load jobs.
    """
    if not lignes:
        return 0

    table_id = assurer_table(bq, table)
    travail = bq.load_table_from_json(
        lignes, table_id, job_config=_config_chargement(table)
    )
    travail.result()
    return len(lignes)


def compter(bq: bigquery.Client, table: str) -> int:
    ref = bq.get_table(f"{config.PROJET}.{config.DATASET_RAW}.{table}")
    return ref.num_rows
