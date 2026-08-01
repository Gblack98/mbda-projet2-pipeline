"""Schémas BigQuery des tables brutes.

Déclarés explicitement plutôt qu'autodétectés. L'autodétection déduit le type
du premier lot reçu : un volume nul sur une séance calme serait typé INTEGER
puis rejetterait un FLOAT le lendemain. Un schéma figé transforme un
changement de format côté source en erreur visible, pas en corruption
silencieuse.
"""

from google.cloud import bigquery

SCHEMA_COTATIONS = [
    bigquery.SchemaField("date_cotation", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("instrument_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("ouverture", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("plus_haut", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("plus_bas", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("cloture", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("volume", "INTEGER", mode="NULLABLE"),
    # Devise telle que renvoyée par la source : USD, USX, GBp, ZAc…
    # La normalisation des sous-unités est faite en aval, dans dbt.
    bigquery.SchemaField("devise_cotation", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("recupere_le", "TIMESTAMP", mode="REQUIRED"),
]

SCHEMA_TAUX = [
    bigquery.SchemaField("date_taux", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("devise_base", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("devise_cible", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("taux", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("recupere_le", "TIMESTAMP", mode="REQUIRED"),
]

# Partitionnement : indispensable à l'idempotence. Le mode Sandbox interdit
# les instructions DML, donc on ne peut pas supprimer les lignes d'une
# journée avant de la recharger. En revanche, un load job peut viser une
# partition précise et la remplacer — voir bigquery_io.charger_partition.
PARTITION = {
    "cotations": "date_cotation",
    "taux_change": "date_taux",
}

CLUSTERING = {
    "cotations": ["instrument_id"],
    "taux_change": ["devise_cible"],
}

SCHEMAS = {
    "cotations": SCHEMA_COTATIONS,
    "taux_change": SCHEMA_TAUX,
}
