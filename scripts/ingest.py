"""Ingestion sans Airflow : python scripts/ingest.py"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402

bq = bigquery_io.client()
bigquery_io.creer_dataset(bq)

cotations = yahoo.recuperer(config.TICKERS, periode=config.PROFONDEUR)
print(f"cotations : {bigquery_io.charger(bq, 'cotations', cotations)} lignes")

debut = (datetime.now(timezone.utc)
         - timedelta(days=config.PROFONDEUR_JOURS)).strftime("%Y-%m-%d")
taux = frankfurter.recuperer(config.DEVISES, debut)
print(f"taux : {bigquery_io.charger(bq, 'taux_change', taux)} lignes")
