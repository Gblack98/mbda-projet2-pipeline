from google.cloud import bigquery
from google.oauth2 import service_account

from . import config, schemas


def client():
    creds = service_account.Credentials.from_service_account_file(config.KEYFILE)
    return bigquery.Client(project=config.PROJET, credentials=creds)


def creer_dataset(bq):
    ref = bigquery.Dataset(f"{config.PROJET}.{config.DATASET}")
    ref.location = config.LOCATION
    bq.create_dataset(ref, exists_ok=True)


def charger(bq, table, lignes):
    """Remplace la table entiere. L'extraction complete tenant en 27 secondes,
    c'est plus simple qu'un chargement incremental et idempotent d'office."""
    if not lignes:
        raise RuntimeError(f"{table} : rien a charger")

    table_id = f"{config.PROJET}.{config.DATASET}.{table}"
    ref = bigquery.Table(table_id, schema=schemas.TABLES[table]["schema"])
    if "cluster" in schemas.TABLES[table]:
        ref.clustering_fields = schemas.TABLES[table]["cluster"]
    bq.create_table(ref, exists_ok=True)

    bq.load_table_from_json(lignes, table_id, job_config=bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=schemas.TABLES[table]["schema"],
    )).result()
    return len(lignes)


def compter(bq, table):
    return bq.get_table(f"{config.PROJET}.{config.DATASET}.{table}").num_rows
