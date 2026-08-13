"""Ingestion complete sans ordonnanceur.

Meme perimetre et memes controles que le DAG. C'est ce script que lance
GitHub Actions, donc celui qui tourne vraiment tous les soirs.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import (  # noqa: E402
    bigquery_io, config, controles, frankfurter, worldbank, yahoo)

CHAMPS_INSTRUMENT = ("instrument_id", "libelle", "classe_actif", "secteur", "sous_secteur")

bq = bigquery_io.client()
bigquery_io.creer_dataset(bq)

volumes = {}


def charger(table, lignes):
    volumes[table] = bigquery_io.charger(bq, table, lignes)
    print(f"{table} : {volumes[table]} lignes")
    return lignes


cotations = charger(
    "cotations", yahoo.recuperer(config.TICKERS, periode=config.PROFONDEUR))

debut = (datetime.now(timezone.utc)
         - timedelta(days=config.PROFONDEUR_JOURS)).strftime("%Y-%m-%d")
charger("taux_change", frankfurter.recuperer(config.DEVISES, debut))

charger("instruments",
        [dict(zip(CHAMPS_INSTRUMENT, i)) for i in config.INSTRUMENTS])
charger("devises", frankfurter.devises(config.DEVISES_DIMENSION))
charger("exportations",
        worldbank.recuperer(config.PAYS, config.INDICATEURS_EXPORT))
charger("secteurs",
        [{"secteur": s, "categorie_export": c}
         for s, c in config.CATEGORIE_EXPORT.items()])

vides = controles.tables_vides(volumes)
if vides:
    raise SystemExit(f"echec : tables vides : {', '.join(vides)}")

manquants = controles.instruments_manquants(
    {ligne["instrument_id"] for ligne in cotations}, config.TICKERS)
if manquants:
    raise SystemExit(
        f"echec : {len(manquants)} instruments sans cotation : {', '.join(manquants)}")

print(f"controles ok : {len(volumes)} tables, {len(config.TICKERS)} instruments cotes")
