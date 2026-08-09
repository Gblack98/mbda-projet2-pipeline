import os
import sys
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task, task_group

# Airflow 3 a sorti BashOperator du coeur pour le mettre dans le provider
# standard, et l'ancien chemin n'existe plus. L'equipe tourne sur les deux
# majeures, le DAG doit s'importer des deux cotes.
try:
    from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
    from airflow.operators.bash import BashOperator

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    alerte, bigquery_io, config, controles, frankfurter, worldbank, yahoo)

CHAMPS_INSTRUMENT = ("instrument_id", "libelle", "classe_actif", "secteur", "sous_secteur")

# dbt vit dans un autre environnement : ses versions de google-cloud-*
# sont incompatibles avec celles d'Airflow.
DBT = f"cd {RACINE}/dbt_pipeline && {RACINE}/venv/bin/dbt"


@dag(
    dag_id="ingest_market_data",
    # Declenchement manuel. Le workflow GitHub Actions tient le calendrier
    # (jours ouvres, 18h37) et tourne sans machine allumee ; ce DAG couvre le
    # meme perimetre et sert a demontrer l'orchestration. Les deux planifies en
    # meme temps ecriraient les memes tables en WRITE_TRUNCATE.
    schedule=None,
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
            charges = bigquery_io.charger(bigquery_io.client(), "cotations", lignes)
            return {
                "lignes": charges,
                "instruments": sorted({l["instrument_id"] for l in lignes}),
            }

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
    def controler_volumes(cotations, n_taux, n_instruments, n_devises,
                          n_secteurs, n_exportations):
        volumes = {
            "cotations": cotations["lignes"],
            "taux_change": n_taux,
            "instruments": n_instruments,
            "devises": n_devises,
            "secteurs": n_secteurs,
            "exportations": n_exportations,
        }
        for table, n in volumes.items():
            print(f"{table} : {n} lignes")

        vides = controles.tables_vides(volumes)
        if vides:
            raise ValueError(f"tables vides : {', '.join(vides)}")

        manquants = controles.instruments_manquants(
            cotations["instruments"], config.TICKERS)
        if manquants:
            raise ValueError(
                f"{len(manquants)} instruments sans cotation : {', '.join(manquants)}")

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
        analytique = BashOperator(
            task_id="run_analytique",
            bash_command=f"{DBT} run --select path:models/analytique")
        tests = BashOperator(task_id="test", bash_command=f"{DBT} test")
        docs = BashOperator(task_id="docs", bash_command=f"{DBT} docs generate")
        deps >> seeds >> staging >> marts >> analytique >> tests >> docs

    @task
    def recapituler():
        bq = bigquery_io.client()
        modele = ("fct_cotation_journaliere", "fct_exportations_pays",
                  "dim_temps", "dim_instrument", "dim_devise")
        analytique = ("agg_volatilite_classe_annee", "agg_tension_mensuelle",
                      "agg_correlation_instrument", "agg_correlation_paire_annee",
                      "agg_exportations_evolution", "kpi_instrument_annee")
        for titre, tables in (("modele", modele), ("analytique", analytique)):
            print(f"-- {titre}")
            for table in tables:
                ref = bq.get_table(f"{config.PROJET}.marts.{table}")
                print(f"marts.{table} : {ref.num_rows} lignes")

    cotations, taux = marches()
    instruments, devises, secteurs, exportations = referentiels()
    charges = [cotations, taux, instruments, devises, secteurs, exportations]

    preparer() >> charges
    controler_volumes(*charges) >> transformation() >> recapituler()


ingest_market_data()
