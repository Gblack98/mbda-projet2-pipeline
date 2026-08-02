import os
import sys
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import bigquery_io, config, frankfurter, worldbank, yahoo  # noqa: E402

CHAMPS_INSTRUMENT = ("instrument_id", "libelle", "classe_actif", "secteur", "sous_secteur")


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
    def references():
        bq = bigquery_io.client()
        instruments = [dict(zip(CHAMPS_INSTRUMENT, i)) for i in config.INSTRUMENTS]
        bigquery_io.charger(bq, "instruments", instruments)
        bigquery_io.charger(bq, "devises", frankfurter.devises(config.DEVISES))
        secteurs = [{"secteur": s, "categorie_export": c}
                    for s, c in config.CATEGORIE_EXPORT.items()]
        bigquery_io.charger(bq, "secteurs", secteurs)
        exportations = worldbank.recuperer(config.PAYS, config.INDICATEURS_EXPORT)
        return bigquery_io.charger(bq, "exportations", exportations)

    @task
    def controler(n_cotations, n_taux, n_exportations):
        print(f"{n_cotations} cotations, {n_taux} taux, {n_exportations} exportations")

    preparer() >> controler(cotations(), taux(), references())


ingest_market_data()
