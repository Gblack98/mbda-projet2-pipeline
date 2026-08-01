"""Ingestion sans Airflow.

    python scripts/ingest.py --quotidien
    python scripts/ingest.py --backfill 10y
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402

JOURS = {"1mo": 30, "2y": 730, "5y": 1825, "10y": 3650}


def il_y_a(jours):
    return (datetime.now(timezone.utc) - timedelta(days=jours)).strftime("%Y-%m-%d")


def main():
    p = argparse.ArgumentParser()
    groupe = p.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--quotidien", action="store_true")
    groupe.add_argument("--backfill", choices=list(JOURS))
    args = p.parse_args()

    if args.quotidien:
        periode = "5d"
        debut = il_y_a(10)
    else:
        periode = args.backfill
        debut = il_y_a(JOURS[periode])

    bq = bigquery_io.client()
    bigquery_io.creer_dataset(bq)

    cotations = yahoo.recuperer(config.TICKERS, periode=periode)
    print(f"cotations : {len(cotations)} lignes")

    taux, ecartees = frankfurter.garder_journees_completes(
        frankfurter.recuperer(config.DEVISES, debut=debut), config.DEVISES)
    print(f"taux : {len(taux)} lignes, {len(ecartees)} journee(s) ecartee(s)")

    if args.quotidien:
        bigquery_io.charger_par_jour(bq, "cotations", cotations)
        bigquery_io.charger_par_jour(bq, "taux_change", taux)
    else:
        bigquery_io.charger_tout(bq, "cotations", cotations)
        bigquery_io.charger_tout(bq, "taux_change", taux)

    for table in ("cotations", "taux_change"):
        print(f"raw.{table} : {bigquery_io.compter(bq, table)} lignes")


if __name__ == "__main__":
    main()
