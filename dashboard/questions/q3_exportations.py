"""Question 3 — quel pays a le panier d'exportation le plus expose ?

La connexion et l'acces aux donnees sont faits. Les graphiques restent a
construire : voir docs/guide-dashboard.md, section « Question 3 ».
"""

import streamlit as st

import donnees

TITRE = "Quel pays a le panier d'exportation le plus exposé ?"
REPONSE = ""  # la phrase de réponse, à écrire sous le titre
FILTRES = ["annee_export"]


def rendre(filtres):
    d = donnees.exportations()

    st.info("Page à construire. Les données sont chargées, voir "
            "`docs/guide-dashboard.md`, section « Question 3 ».")

    st.dataframe(d[d["annee"] == filtres["annee_export"]],
                 width="stretch", hide_index=True)
