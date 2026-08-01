"""DAG de reprise d'historique — dix ans de cotations et de taux.

Ne tourne pas sur planification : on le déclenche à la main, une fois, pour
amorcer l'entrepôt, puis après chaque expiration des tables (le mode Sandbox
les supprime au bout de soixante jours).

Contrairement au DAG quotidien, il remplace les tables intégralement plutôt
que partition par partition : écrire dix ans une journée à la fois
représenterait plusieurs milliers de load jobs.
"""

from datetime import datetime, timedelta
import os
import sys

from airflow.decorators import dag, task
from airflow.models.param import Param

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import bigquery_io, config, frankfurter, yahoo  # noqa: E402

ARGS = {
    "owner": "gblack98",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

# Frankfurter attend des dates, Yahoo une durée relative.
DEBUTS = {"1mo": "2025-01-01", "2y": "2024-01-01", "5y": "2020-01-01", "10y": "2016-01-01"}


@dag(
    dag_id="backfill_history",
    description="Reprise d'historique — à déclencher manuellement",
    schedule=None,
    start_date=datetime(2026, 8, 1),
    catchup=False,
    max_active_runs=1,
    default_args=ARGS,
    params={
        "profondeur": Param(
            "10y", enum=list(DEBUTS),
            description="Profondeur d'historique à reprendre",
        )
    },
    tags=["ingestion", "manuel"],
)
def backfill_history():

    @task
    def preparer() -> None:
        bq = bigquery_io.client()
        bigquery_io.assurer_dataset(bq, config.DATASET_RAW)

    @task
    def reprendre_cotations(**contexte) -> int:
        profondeur = contexte["params"]["profondeur"]
        lignes = yahoo.recuperer(config.TICKERS, periode=profondeur)
        bq = bigquery_io.client()
        total = bigquery_io.charger_integralement(bq, config.TABLE_COTATIONS, lignes)
        print(f"{total} cotations sur {profondeur}")
        return total

    @task
    def reprendre_taux(**contexte) -> int:
        profondeur = contexte["params"]["profondeur"]
        lignes = frankfurter.recuperer(config.DEVISES, debut=DEBUTS[profondeur])

        completes, partielles = frankfurter.journees_completes(lignes, config.DEVISES)
        retenues = set(completes)
        lignes = [l for l in lignes if l["date_taux"] in retenues]

        bq = bigquery_io.client()
        total = bigquery_io.charger_integralement(bq, config.TABLE_TAUX, lignes)
        print(f"{total} taux sur {len(completes)} journées complètes "
              f"({len(partielles)} partielles écartées)")
        return total

    @task
    def recapituler(cotations: int, taux: int) -> None:
        if cotations == 0 or taux == 0:
            raise ValueError(
                f"reprise incomplète : {cotations} cotations, {taux} taux"
            )
        print(f"entrepôt amorcé : {cotations:,} cotations, {taux:,} taux")

    debut = preparer()
    cotations = reprendre_cotations()
    taux = reprendre_taux()
    debut >> [cotations, taux]
    recapituler(cotations, taux)


backfill_history()
