import os
import sys
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task, task_group
from airflow.operators.bash import BashOperator

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import alerte, bigquery_io, config, frankfurter, worldbank, yahoo  # noqa: E402

CHAMPS_INSTRUMENT = ("instrument_id", "libelle", "classe_actif", "secteur", "sous_secteur")

# dbt vit dans un autre environnement : ses versions de google-cloud-*
# sont incompatibles avec celles d'Airflow.
DBT = f"cd {RACINE}/dbt_pipeline && {RACINE}/venv/bin/dbt"


@dag(
    dag_id="ingest_market_data",
    schedule="0 18 * * 1-5",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={
        "owner": "gblack98",
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": alerte.sur_echec,
    },
    tags=["ingestion", "dbt", "quotidien"],
)
def ingest_market_data():

    @task
    def preparer():
        bigquery_io.creer_dataset(bigquery_io.client())

    @task_group(group_id="marches")
    def marches():
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

        return cotations(), taux()

    @task_group(group_id="referentiels")
    def referentiels():
        @task
        def instruments():
            lignes = [dict(zip(CHAMPS_INSTRUMENT, i)) for i in config.INSTRUMENTS]
            return bigquery_io.charger(bigquery_io.client(), "instruments", lignes)

        @task
        def devises():
            lignes = frankfurter.devises(config.DEVISES_DIMENSION)
            return bigquery_io.charger(bigquery_io.client(), "devises", lignes)

        @task
        def secteurs():
            lignes = [{"secteur": s, "categorie_export": c}
                      for s, c in config.CATEGORIE_EXPORT.items()]
            return bigquery_io.charger(bigquery_io.client(), "secteurs", lignes)

        @task
        def exportations():
            lignes = worldbank.recuperer(config.PAYS, config.INDICATEURS_EXPORT)
            return bigquery_io.charger(bigquery_io.client(), "exportations", lignes)

        return instruments(), devises(), secteurs(), exportations()

    @task
    def controler_volumes(n_cotations, n_taux, n_instruments, n_devises,
                          n_secteurs, n_exportations):
        volumes = {
            "cotations": n_cotations,
            "taux_change": n_taux,
            "instruments": n_instruments,
            "devises": n_devises,
            "secteurs": n_secteurs,
            "exportations": n_exportations,
        }
        for table, n in volumes.items():
            print(f"{table} : {n} lignes")

        vides = [t for t, n in volumes.items() if not n]
        if vides:
            raise ValueError(f"tables vides : {', '.join(vides)}")

        if n_instruments != len(config.TICKERS):
            raise ValueError(
                f"{n_instruments} instruments charges, {len(config.TICKERS)} attendus")

    @task_group(group_id="transformation")
    def transformation():
        deps = BashOperator(task_id="deps", bash_command=f"{DBT} deps")
        seeds = BashOperator(task_id="seed", bash_command=f"{DBT} seed")
        staging = BashOperator(
            task_id="run_staging",
            bash_command=f"{DBT} run --select path:models/staging")
        marts = BashOperator(
            task_id="run_marts",
            bash_command=f"{DBT} run --select path:models/marts")
        tests = BashOperator(task_id="test", bash_command=f"{DBT} test")
        docs = BashOperator(task_id="docs", bash_command=f"{DBT} docs generate")
        deps >> seeds >> staging >> marts >> tests >> docs

    @task
    def recapituler():
        bq = bigquery_io.client()
        for table in ("fct_cotation_journaliere", "fct_exportations_pays",
                      "dim_temps", "dim_instrument", "dim_devise"):
            ref = bq.get_table(f"{config.PROJET}.marts.{table}")
            print(f"marts.{table} : {ref.num_rows} lignes")

    cotations, taux = marches()
    instruments, devises, secteurs, exportations = referentiels()
    charges = [cotations, taux, instruments, devises, secteurs, exportations]

    preparer() >> charges
    controler_volumes(*charges) >> transformation() >> recapituler()


ingest_market_data()
