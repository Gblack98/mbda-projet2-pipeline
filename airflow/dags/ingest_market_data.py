import os
import sys
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402


@dag(
    dag_id="ingest_market_data",
    schedule="0 18 * * 1-5",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"owner": "gblack98", "retries": 3,
                  "retry_delay": timedelta(minutes=5)},
    tags=["ingestion"],
)
def ingest_market_data():

    @task
    def preparer():
        bigquery_io.creer_dataset(bigquery_io.client())

    @task
    def cotations():
        lignes = yahoo.recuperer(config.TICKERS, periode=config.PROFONDEUR)
        return bigquery_io.charger(bigquery_io.client(), "cotations", lignes)

    @task
    def taux():
        debut = (datetime.now(timezone.utc)
                 - timedelta(days=config.PROFONDEUR_JOURS)).strftime("%Y-%m-%d")
        lignes = frankfurter.recuperer(config.DEVISES, debut)
        return bigquery_io.charger(bigquery_io.client(), "taux_change", lignes)

    @task
    def controler(n_cotations, n_taux):
        print(f"{n_cotations} cotations, {n_taux} taux")

    preparer() >> controler(cotations(), taux())


ingest_market_data()
