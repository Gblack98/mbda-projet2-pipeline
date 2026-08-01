from collections import defaultdict

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


def creer_table(bq, table):
    infos = schemas.TABLES[table]
    table_id = f"{config.PROJET}.{config.DATASET}.{table}"
    ref = bigquery.Table(table_id, schema=infos["schema"])
    ref.time_partitioning = bigquery.TimePartitioning(field=infos["partition"])
    ref.clustering_fields = infos["cluster"]
    bq.create_table(ref, exists_ok=True)
    return table_id


def _config(table):
    return bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=schemas.TABLES[table]["schema"],
    )


def charger_par_jour(bq, table, lignes):
    """Ecrit chaque journee dans sa partition. Le Sandbox interdit le DML,
    donc on remplace la partition au lieu de supprimer puis reinserer."""
    if not lignes:
        return 0

    champ = schemas.TABLES[table]["partition"]
    table_id = creer_table(bq, table)

    par_jour = defaultdict(list)
    for ligne in lignes:
        par_jour[ligne[champ]].append(ligne)

    for jour, lot in par_jour.items():
        suffixe = jour.replace("-", "")
        bq.load_table_from_json(lot, f"{table_id}${suffixe}",
                                job_config=_config(table)).result()
    return len(par_jour)


def charger_tout(bq, table, lignes):
    if not lignes:
        return 0
    table_id = creer_table(bq, table)
    bq.load_table_from_json(lignes, table_id, job_config=_config(table)).result()
    return len(lignes)


def compter(bq, table):
    return bq.get_table(f"{config.PROJET}.{config.DATASET}.{table}").num_rows
