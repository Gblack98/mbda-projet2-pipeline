"""Page d'accueil : verifie que la lecture de BigQuery marche et laisse
parcourir les tables du dataset marts.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import donnees  # noqa: E402

# Ce qui s'affiche dans la liste deroulante, et la fonction correspondante.
TABLES = {
    "dim_devise": donnees.devises,
    "dim_instrument": donnees.instruments,
    "agg_volatilite_classe_annee": donnees.volatilite_classe,
    "agg_tension_mensuelle": donnees.tension,
    "agg_correlation_instrument": donnees.correlations,
    "agg_correlation_paire_annee": donnees.correlations_par_annee,
    "agg_exportations_evolution": donnees.exportations,
    "kpi_instrument_annee": donnees.kpi_instrument,
}

st.title("Matières premières et devises")
st.caption("Master 1 MBDA · UN-CHK · 2026")

try:
    c = donnees.couverture().iloc[0]
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

st.markdown(
    "La connexion à BigQuery est en place et le dataset `marts` est lisible. "
    "Les cinq questions métier sont dans le menu ci-dessus.")

g, d = st.columns(2)
g.metric("Cotations", f"{int(c.lignes):,}".replace(",", " "))
d.metric("Instruments", int(c.instruments))
st.caption(f"Du {c.debut:%d/%m/%Y} au {c.fin:%d/%m/%Y}. "
           "Lecture seule, dataset `marts`.")

st.divider()

nom = st.selectbox("Table", list(TABLES))
st.dataframe(TABLES[nom](), width="stretch", hide_index=True)

if st.button("Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()
