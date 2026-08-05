import os
import sys
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
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

    @task
    def controler_qualite(n_cotations, n_taux, n_instruments, n_devises,
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

    deps = BashOperator(task_id="dbt_deps", bash_command=f"{DBT} deps")
    executer = BashOperator(task_id="dbt_run", bash_command=f"{DBT} run")
    verifier = BashOperator(task_id="dbt_test", bash_command=f"{DBT} test")

    depart = preparer()
    charges = [cotations(), taux(), instruments(),
               devises(), secteurs(), exportations()]
    depart >> charges

    controler_qualite(*charges) >> deps >> executer >> verifier


ingest_market_data()
