"""DAG quotidien — collecte des cotations et des taux de change.

Se déclenche après la clôture des marchés américains. Chaque exécution
remplace les partitions journalières concernées : rejouer une date aboutit au
même état, sans doublon.

Les deux collectes sont indépendantes et tournent en parallèle. L'échec de
l'une n'empêche pas l'autre d'aboutir : une panne côté Yahoo ne doit pas
priver l'entrepôt des taux de change du jour.
"""

from datetime import datetime, timedelta, timezone
import os
import sys

from airflow.decorators import dag, task

# Les modules partagés vivent à côté des DAGs. Airflow n'ajoute pas
# automatiquement ce répertoire au chemin d'import lorsqu'il analyse un DAG.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402

ARGS = {
    "owner": "gblack98",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


@dag(
    dag_id="ingest_market_data",
    description="Collecte quotidienne des cotations et des taux de change",
    schedule="0 18 * * 1-5",  # jours ouvrés, après clôture
    start_date=datetime(2026, 8, 1),
    catchup=False,
    max_active_runs=1,
    default_args=ARGS,
    tags=["ingestion", "quotidien"],
)
def ingest_market_data():

    @task
    def preparer() -> str:
        """Crée le dataset s'il manque. Idempotent."""
        bq = bigquery_io.client()
        bigquery_io.assurer_dataset(bq, config.DATASET_RAW)
        return config.DATASET_RAW

    @task
    def collecter_cotations(_dataset: str) -> dict:
        """Récupère les dernières séances et remplace leurs partitions.

        On demande cinq jours plutôt qu'un seul : un jour férié américain ou
        un week-end décalerait la dernière séance disponible, et une fenêtre
        glissante rattrape ces trous sans intervention.
        """
        lignes = yahoo.recuperer(config.TICKERS, periode="5d")
        bq = bigquery_io.client()
        charge = bigquery_io.charger_par_partition(bq, config.TABLE_COTATIONS, lignes)
        return {"partitions": len(charge), "lignes": sum(charge.values())}

    @task
    def collecter_taux(_dataset: str) -> dict:
        """Récupère les taux et n'écrit que les journées entièrement publiées.

        Les devises ne sortent pas toutes en même temps. Charger une journée
        incomplète créerait un trou définitif, le DAG ne repassant pas sur le
        passé.
        """
        debut = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
        lignes = frankfurter.recuperer(config.DEVISES, debut=debut)

        completes, partielles = frankfurter.journees_completes(lignes, config.DEVISES)
        if partielles:
            print(f"journées partielles écartées : {', '.join(partielles)}")

        retenues = set(completes)
        lignes = [l for l in lignes if l["date_taux"] in retenues]
        if not lignes:
            print("aucune journée complète disponible")
            return {"partitions": 0, "lignes": 0}

        bq = bigquery_io.client()
        charge = bigquery_io.charger_par_partition(bq, config.TABLE_TAUX, lignes)
        return {"partitions": len(charge), "lignes": sum(charge.values())}

    @task
    def controler(cotations: dict, taux: dict) -> None:
        """Refuse une exécution qui n'aurait rien chargé du tout.

        Un DAG vert sur un entrepôt vide est le pire des cas : personne ne
        regarde une exécution réussie.
        """
        print(f"cotations : {cotations['lignes']} lignes, "
              f"{cotations['partitions']} partitions")
        print(f"taux      : {taux['lignes']} lignes, "
              f"{taux['partitions']} partitions")

        if cotations["lignes"] == 0 and taux["lignes"] == 0:
            raise ValueError(
                "aucune donnée chargée : sources indisponibles ou séance vide"
            )

    dataset = preparer()
    controler(collecter_cotations(dataset), collecter_taux(dataset))


ingest_market_data()
