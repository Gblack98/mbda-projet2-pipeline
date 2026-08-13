"""Acces a BigQuery pour le tableau de bord.

Un seul endroit lit l'entrepot. Les pages ne voient que des DataFrames, elles
n'ecrivent jamais de SQL. Si une requete doit changer, elle change ici.

Le compte de service utilise est en lecture seule et limite au dataset marts :
il ne peut ni ecrire, ni lire raw ou marts_staging. Verifiable avec
`python dashboard/donnees.py`.
"""

import json
import os

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

PROJET = "crucial-bonsai-418120"
MARTS = f"`{PROJET}`.marts"

# Duree de cache. Le pipeline tourne une fois par jour ouvre : dix minutes
# suffisent largement et permettent de montrer une donnee fraiche en soutenance
# sans marteler l'entrepot a chaque clic.
CACHE = 600


def _identifiants():
    """Trois sources possibles, dans cet ordre.

    1. st.secrets["gcp_service_account"] : ce que lit Streamlit Community Cloud.
    2. MBDA_DASHBOARD_KEYFILE : un chemin, pratique en local.
    3. ~/.gcp/mbda-dashboard-ro.json : le chemin par defaut du projet.
    """
    try:
        if "gcp_service_account" in st.secrets:
            infos = dict(st.secrets["gcp_service_account"])
            return service_account.Credentials.from_service_account_info(infos)
    except Exception:
        pass  # pas de fichier secrets en local, ce n'est pas une erreur

    chemin = os.path.expanduser(os.environ.get(
        "MBDA_DASHBOARD_KEYFILE", "~/.gcp/mbda-dashboard-ro.json"))
    if not os.path.exists(chemin):
        raise FileNotFoundError(
            f"Aucun identifiant trouve. Ni st.secrets, ni {chemin}. "
            "Voir docs/guide-dashboard.md, section 1.")
    return service_account.Credentials.from_service_account_file(chemin)


@st.cache_resource
def client():
    return bigquery.Client(project=PROJET, credentials=_identifiants())


@st.cache_data(ttl=CACHE, show_spinner="Lecture de BigQuery…")
def _lire(sql: str) -> pd.DataFrame:
    # create_bqstorage_client=False : l'API Storage accelere le transfert mais
    # exige la permission bigquery.readsessions.create, que le compte en lecture
    # seule n'a pas et ne doit pas avoir. Les volumes ici sont minuscules, le
    # transfert REST suffit largement.
    return client().query(sql).to_dataframe(create_bqstorage_client=False)


# --------------------------------------------------------------------------
# Une fonction par table. Les pages appellent celles dont elles ont besoin.
# --------------------------------------------------------------------------

def devises() -> pd.DataFrame:
    return _lire(f"""
        select devise_id, nom_devise, symbole, coefficient_variation, regime
        from {MARTS}.dim_devise
        order by coefficient_variation, devise_id""")


def instruments() -> pd.DataFrame:
    return _lire(f"""
        select instrument_id, libelle, classe_actif, secteur, sous_secteur,
               categorie_export
        from {MARTS}.dim_instrument
        order by classe_actif, libelle""")


def volatilite_classe() -> pd.DataFrame:
    return _lire(f"""
        select classe_actif, annee, instruments, observations,
               observations_ecartees, volatilite, volatilite_hors_anomalie,
               amplitude_moyenne, variation_moyenne
        from {MARTS}.agg_volatilite_classe_annee
        order by classe_actif, annee""")


def volatilite_totale() -> pd.DataFrame:
    """Volatilite d'ensemble par classe.

    Ce n'est pas la moyenne des annees : un ecart-type ne se moyenne pas. Il
    faut le recalculer sur toutes les observations.
    """
    return _lire(f"""
        select i.classe_actif,
               count(distinct f.instrument_id) as instruments,
               stddev(f.variation_pct) as volatilite,
               stddev(if(f.variation_exploitable, f.variation_pct, null))
                   as volatilite_hors_anomalie
        from {MARTS}.fct_cotation_journaliere f
        join {MARTS}.dim_instrument i using (instrument_id)
        where f.variation_pct is not null
        group by i.classe_actif
        order by volatilite desc""")


def tension() -> pd.DataFrame:
    return _lire(f"""
        select mois, annee, instruments, observations, observations_ecartees,
               volatilite, volatilite_hors_anomalie, mediane_historique,
               multiple_mediane, est_tension, ecart_mois_precedent
        from {MARTS}.agg_tension_mensuelle
        order by mois""")


def correlations() -> pd.DataFrame:
    return _lire(f"""
        select paire_id, libelle, instrument_action, instrument_matiere, temoin,
               jours_communs, debut, fin, correlation, part_variance_expliquee,
               volatilite_action, volatilite_matiere
        from {MARTS}.agg_correlation_instrument
        order by correlation desc""")


def correlations_par_annee() -> pd.DataFrame:
    return _lire(f"""
        select paire_id, libelle, temoin, annee, jours_communs, correlation,
               ecart_annee_precedente
        from {MARTS}.agg_correlation_paire_annee
        order by paire_id, annee""")


def exportations() -> pd.DataFrame:
    return _lire(f"""
        select pays, annee, categorie_export, part_exportations, rang_categorie,
               est_categorie_dominante, part_couverte_annee, annee_precedente,
               part_annee_precedente, ecart_points, evolution_pct
        from {MARTS}.agg_exportations_evolution
        order by pays, annee, rang_categorie""")


def kpi_instrument() -> pd.DataFrame:
    return _lire(f"""
        select instrument_id, libelle, classe_actif, secteur, annee, jours_cotes,
               annee_complete, volatilite, volatilite_hors_anomalie,
               amplitude_moyenne, volume_moyen, performance_pct,
               performance_eur_pct, ecart_performance_annee_precedente
        from {MARTS}.kpi_instrument_annee
        order by annee, instrument_id""")


@st.cache_data(ttl=CACHE, show_spinner="Lecture des cotations…")
def variations_paire(action: str, matiere: str, borne: float = 25.0) -> pd.DataFrame:
    """Variations quotidiennes appariees, pour un nuage de points.

    Requete parametree : les identifiants ne sont jamais colles dans le SQL.
    """
    sql = f"""
        with v as (
            select date_cotation, instrument_id, variation_pct
            from {MARTS}.fct_cotation_journaliere
            where variation_exploitable
        )
        select a.date_cotation, a.variation_pct as action,
               m.variation_pct as matiere
        from v as a
        join v as m on m.date_cotation = a.date_cotation
        where a.instrument_id = @action and m.instrument_id = @matiere
          and abs(a.variation_pct) <= @borne and abs(m.variation_pct) <= @borne
        order by a.date_cotation"""
    config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("action", "STRING", action),
        bigquery.ScalarQueryParameter("matiere", "STRING", matiere),
        bigquery.ScalarQueryParameter("borne", "FLOAT64", borne),
    ])
    return client().query(sql, job_config=config).to_dataframe(
        create_bqstorage_client=False)


def couverture() -> pd.DataFrame:
    return _lire(f"""
        select min(date_cotation) as debut, max(date_cotation) as fin,
               count(*) as lignes, count(distinct instrument_id) as instruments,
               countif(not variation_exploitable) as non_exploitables
        from {MARTS}.fct_cotation_journaliere""")


if __name__ == "__main__":
    # Verification hors Streamlit : les droits sont-ils ceux qu'on croit ?
    bq = bigquery.Client(project=PROJET, credentials=_identifiants())
    print("compte :", json.load(open(os.path.expanduser(
        os.environ.get("MBDA_DASHBOARD_KEYFILE",
                       "~/.gcp/mbda-dashboard-ro.json"))))["client_email"])
    for nom, sql in [
        ("marts.dim_devise", f"select count(*) c from {MARTS}.dim_devise"),
        ("raw.cotations (doit echouer)",
         f"select count(*) c from `{PROJET}`.raw.cotations"),
    ]:
        try:
            print(f"  OK      {nom} -> {list(bq.query(sql))[0].c}")
        except Exception as e:
            print(f"  REFUSE  {nom} -> {type(e).__name__}")
