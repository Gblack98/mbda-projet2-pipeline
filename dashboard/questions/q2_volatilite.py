"""Question 2 — quelle classe d'actif est la plus volatile ?

La connexion et l'acces aux donnees sont faits. Les graphiques restent a
construire : voir docs/guide-dashboard.md, section « Question 2 ».
"""

import streamlit as st

import donnees

TITRE = "Quelle classe d'actif est la plus volatile ?"
REPONSE = ""  # la phrase de réponse, à écrire sous le titre
FILTRES = ["annees", "classes", "mesure"]


def rendre(filtres):
    par_annee = donnees.volatilite_classe()
    ensemble = donnees.volatilite_totale()

    st.info("Page à construire. Les données sont chargées, voir "
            "`docs/guide-dashboard.md`, section « Question 2 ».")

    st.caption("agg_volatilite_classe_annee")
    st.dataframe(par_annee, width="stretch", hide_index=True)
    st.caption("volatilité d'ensemble, recalculée sur toutes les observations")
    st.dataframe(ensemble, width="stretch", hide_index=True)
