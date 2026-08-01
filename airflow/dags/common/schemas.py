from google.cloud import bigquery

COTATIONS = [
    bigquery.SchemaField("date_cotation", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("instrument_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("ouverture", "FLOAT"),
    bigquery.SchemaField("plus_haut", "FLOAT"),
    bigquery.SchemaField("plus_bas", "FLOAT"),
    bigquery.SchemaField("cloture", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("volume", "INTEGER"),
    bigquery.SchemaField("devise_cotation", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("recupere_le", "TIMESTAMP", mode="REQUIRED"),
]

TAUX = [
    bigquery.SchemaField("date_taux", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("devise_base", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("devise_cible", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("taux", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("recupere_le", "TIMESTAMP", mode="REQUIRED"),
]

# Pas de partitionnement : le Sandbox supprime toute partition de plus de
# 60 jours, ce qui effacerait l'historique.
TABLES = {
    "cotations": {"schema": COTATIONS, "cluster": ["instrument_id", "date_cotation"]},
    "taux_change": {"schema": TAUX, "cluster": ["devise_cible", "date_taux"]},
}
