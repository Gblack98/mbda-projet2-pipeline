"""Question 5 — quelles ont ete les periodes de tension ?

La connexion et l'acces aux donnees sont faits. Les graphiques restent a
construire : voir docs/guide-dashboard.md, section « Question 5 ».
"""

import streamlit as st

import donnees

TITRE = "Quelles ont été les périodes de tension ?"
REPONSE = ""  # la phrase de réponse, à écrire sous le titre
FILTRES = ["annees", "mesure"]


def rendre(filtres):
    d = donnees.tension()

    st.info("Page à construire. Les données sont chargées, voir "
            "`docs/guide-dashboard.md`, section « Question 5 ».")

    st.dataframe(d, width="stretch", hide_index=True)
