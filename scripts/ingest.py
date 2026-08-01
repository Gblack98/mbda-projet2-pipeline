"""Ingestion hors ordonnanceur.

Reprend exactement la logique des DAGs, sans Airflow. Sert à amorcer
l'entrepôt, à rejouer une journée, ou à travailler quand faire tourner un
ordonnanceur complet n'a pas d'intérêt.

    python scripts/ingest.py --quotidien           # la séance la plus récente
    python scripts/ingest.py --backfill 10y        # dix ans d'historique
    python scripts/ingest.py --backfill 2y --sans-taux
"""

import argparse
from datetime import datetime, timedelta, timezone
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "airflow", "dags"))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402

# Correspondance entre la profondeur demandée et la plage de taux de change.
# Frankfurter attend des dates, Yahoo une durée relative.
#
# La fenêtre quotidienne est délibérément courte. Le chargement par partition
# émet un load job par journée : demander six mois de taux pour une exécution
# quotidienne déclencherait cent cinquante jobs au lieu de cinq.
DEBUTS = {"1mo": "2025-01-01", "2y": "2024-01-01", "5y": "2020-01-01", "10y": "2016-01-01"}
FENETRE_QUOTIDIENNE = 10  # jours


def ingerer_cotations(bq, periode, partition):
    print(f"Cotations — {len(config.TICKERS)} instruments, période {periode}")
    lignes = yahoo.recuperer(config.TICKERS, periode=periode)
    instruments = len({l["instrument_id"] for l in lignes})
    print(f"  {len(lignes)} lignes sur {instruments} instruments")

    if partition:
        charge = bigquery_io.charger_par_partition(bq, config.TABLE_COTATIONS, lignes)
        print(f"  {len(charge)} partition(s) remplacée(s)")
    else:
        bigquery_io.charger_integralement(bq, config.TABLE_COTATIONS, lignes)
        print("  table remplacée intégralement")


def ingerer_taux(bq, debut, fin, partition):
    print(f"Taux de change — {len(config.DEVISES)} devises")
    lignes = frankfurter.recuperer(config.DEVISES, debut=debut, fin=fin)
    completes, partielles = frankfurter.journees_completes(lignes, config.DEVISES)

    if partielles:
        print(f"  {len(partielles)} journée(s) partielle(s) écartée(s) : "
              f"{', '.join(partielles[-3:])}")
        retenues = set(completes)
        lignes = [l for l in lignes if l["date_taux"] in retenues]

    if not lignes:
        print("  aucune journée complète : rien à charger")
        return

    print(f"  {len(lignes)} lignes sur {len(completes)} journées complètes")

    if partition:
        charge = bigquery_io.charger_par_partition(bq, config.TABLE_TAUX, lignes)
        print(f"  {len(charge)} partition(s) remplacée(s)")
    else:
        bigquery_io.charger_integralement(bq, config.TABLE_TAUX, lignes)
        print("  table remplacée intégralement")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    groupe = p.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--quotidien", action="store_true",
                        help="dernières séances, chargées par partition")
    groupe.add_argument("--backfill", choices=list(DEBUTS),
                        help="reprise d'historique, table remplacée intégralement")
    p.add_argument("--sans-taux", action="store_true")
    p.add_argument("--sans-cotations", action="store_true")
    args = p.parse_args()

    if args.quotidien:
        periode = "5d"
        debut_taux = (datetime.now(timezone.utc) - timedelta(days=FENETRE_QUOTIDIENNE)).strftime("%Y-%m-%d")
        partition = True
    else:
        periode = args.backfill
        debut_taux = DEBUTS[periode]
        partition = False

    print(f"Projet {config.PROJET} — dataset {config.DATASET_RAW}\n")
    bq = bigquery_io.client()
    bigquery_io.assurer_dataset(bq, config.DATASET_RAW)

    if not args.sans_cotations:
        ingerer_cotations(bq, periode, partition)
    if not args.sans_taux:
        ingerer_taux(bq, debut_taux, None, partition)

    print("\nÉtat de l'entrepôt")
    for table in (config.TABLE_COTATIONS, config.TABLE_TAUX):
        try:
            print(f"  raw.{table} : {bigquery_io.compter(bq, table):,} lignes")
        except Exception:
            print(f"  raw.{table} : absente")


if __name__ == "__main__":
    main()
