"""Question 1 — le regime de change protege-t-il de la volatilite ?

La connexion et l'acces aux donnees sont faits. Les graphiques restent a
construire : voir docs/guide-dashboard.md, section « Question 1 ».
"""

import streamlit as st

import donnees

TITRE = "Le régime de change protège-t-il de la volatilité ?"
REPONSE = ""  # la phrase de réponse, à écrire sous le titre


def rendre(filtres):
    d = donnees.devises()

    st.info("Page à construire. Les données sont chargées, voir "
            "`docs/guide-dashboard.md`, section « Question 1 ».")

    st.dataframe(d, width="stretch", hide_index=True)
