"""Ingestion sans Airflow : python scripts/ingest.py"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import bigquery_io, config, frankfurter, worldbank, yahoo  # noqa: E402

CHAMPS_INSTRUMENT = ("instrument_id", "libelle", "classe_actif", "secteur", "sous_secteur")

bq = bigquery_io.client()
bigquery_io.creer_dataset(bq)

cotations = yahoo.recuperer(config.TICKERS, periode=config.PROFONDEUR)
print(f"cotations : {bigquery_io.charger(bq, 'cotations', cotations)} lignes")

debut = (datetime.now(timezone.utc)
         - timedelta(days=config.PROFONDEUR_JOURS)).strftime("%Y-%m-%d")
taux = frankfurter.recuperer(config.DEVISES, debut)
print(f"taux : {bigquery_io.charger(bq, 'taux_change', taux)} lignes")

instruments = [dict(zip(CHAMPS_INSTRUMENT, i)) for i in config.INSTRUMENTS]
print(f"instruments : {bigquery_io.charger(bq, 'instruments', instruments)} lignes")

devises = frankfurter.devises(config.DEVISES)
print(f"devises : {bigquery_io.charger(bq, 'devises', devises)} lignes")

exportations = worldbank.recuperer(config.PAYS, config.INDICATEURS_EXPORT)
print(f"exportations : {bigquery_io.charger(bq, 'exportations', exportations)} lignes")
