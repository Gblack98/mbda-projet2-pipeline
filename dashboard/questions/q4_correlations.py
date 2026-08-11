"""Question 4 — les societes extractives suivent-elles leur matiere ?

La connexion et l'acces aux donnees sont faits. Les graphiques restent a
construire : voir docs/guide-dashboard.md, section « Question 4 ».
"""

import streamlit as st

import donnees

TITRE = "Les sociétés extractives suivent-elles leur matière première ?"
REPONSE = ""  # la phrase de réponse, à écrire sous le titre


def rendre(filtres):
    paires = donnees.correlations()
    par_annee = donnees.correlations_par_annee()

    st.info("Page à construire. Les données sont chargées, voir "
            "`docs/guide-dashboard.md`, section « Question 4 ».")

    st.caption("agg_correlation_instrument")
    st.dataframe(paires, width="stretch", hide_index=True)
    st.caption("agg_correlation_paire_annee")
    st.dataframe(par_annee, width="stretch", hide_index=True)
