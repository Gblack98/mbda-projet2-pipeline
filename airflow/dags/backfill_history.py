import os
import sys
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.models.param import Param

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402

JOURS = {"1mo": 30, "2y": 730, "5y": 1825, "10y": 3650}


def il_y_a(jours):
    return (datetime.now(timezone.utc) - timedelta(days=jours)).strftime("%Y-%m-%d")


@dag(
    dag_id="backfill_history",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"owner": "gblack98", "retries": 2,
                  "retry_delay": timedelta(minutes=10)},
    params={"profondeur": Param("10y", enum=list(JOURS))},
    tags=["ingestion"],
)
def backfill_history():

    @task
    def preparer():
        bigquery_io.creer_dataset(bigquery_io.client())

    @task
    def cotations(**contexte):
        profondeur = contexte["params"]["profondeur"]
        lignes = yahoo.recuperer(config.TICKERS, periode=profondeur)
        bigquery_io.charger_tout(bigquery_io.client(), "cotations", lignes)
        return len(lignes)

    @task
    def taux(**contexte):
        debut = il_y_a(JOURS[contexte["params"]["profondeur"]])
        lignes, _ = frankfurter.garder_journees_completes(
            frankfurter.recuperer(config.DEVISES, debut=debut), config.DEVISES)
        bigquery_io.charger_tout(bigquery_io.client(), "taux_change", lignes)
        return len(lignes)

    @task
    def controler(n_cotations, n_taux):
        print(f"{n_cotations} cotations, {n_taux} taux")
        if n_cotations == 0 or n_taux == 0:
            raise ValueError("reprise incomplete")

    preparer() >> controler(cotations(), taux())


backfill_history()
