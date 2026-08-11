"""Tableau de bord — matieres premieres et devises ouest-africaines.

Lance en local :

    ./venv-dashboard/bin/streamlit run dashboard/app.py

Le fichier ne contient que la navigation et les filtres. Les graphiques sont
dans dashboard/questions/, un fichier par question metier.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import donnees  # noqa: E402
import style as s  # noqa: E402
from questions import (q1_regime, q2_volatilite, q3_exportations,  # noqa: E402
                       q4_correlations, q5_tension)

PAGES = [q1_regime, q2_volatilite, q3_exportations, q4_correlations, q5_tension]

st.set_page_config(page_title="Matières premières et devises",
                   page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(s.CSS, unsafe_allow_html=True)


def barre_laterale():
    """Filtres branches sur les dimensions du modele en etoile.

    C'est ce qui distingue un tableau de bord d'une suite de graphiques : on
    doit pouvoir decouper les mesures par les axes du modele. Les filtres sont
    au meme endroit pour toutes les pages, jamais dans une carte.
    """
    with st.sidebar:
        st.markdown("### Matières premières et devises")
        st.caption("Master 1 MBDA · UN-CHK · 2026")

        choix = st.radio("Question", options=range(len(PAGES)),
                         format_func=lambda i: f"{i + 1}. {TITRES_COURTS[i]}",
                         label_visibility="collapsed")
        st.divider()

        page = PAGES[choix]
        applicables = getattr(page, "FILTRES", [])
        filtres = {}

        if "annees" in applicables:
            volat = donnees.volatilite_classe()
            bornes = (int(volat["annee"].min()), int(volat["annee"].max()))
            filtres["annees"] = st.slider("Période", *bornes, value=bornes)
        else:
            filtres["annees"] = (1900, 2100)

        if "classes" in applicables:
            toutes = sorted(donnees.volatilite_classe()["classe_actif"].unique())
            filtres["classes"] = st.multiselect(
                "Classe d'actif", options=toutes, default=toutes,
                format_func=lambda c: s.NOM_CLASSE.get(c, c)) or toutes
        else:
            filtres["classes"] = None

        if "mesure" in applicables:
            mesure = st.radio(
                "Mesure", ["Toutes les observations", "Hors anomalie de prix"],
                help="L'anomalie est le pétrole WTI à prix négatif, "
                     "le 20 avril 2020. Deux séances sur 103 104.")
            filtres["hors_anomalie"] = mesure.startswith("Hors")
        else:
            filtres["hors_anomalie"] = False

        if "annee_export" in applicables:
            annees = sorted(donnees.exportations()["annee"].unique(), reverse=True)
            filtres["annee_export"] = st.selectbox("Année", annees)

        st.divider()
        c = donnees.couverture().iloc[0]
        st.caption(
            f"**{int(c.lignes):,}".replace(",", " ") + " cotations** · "
            f"{int(c.instruments)} instruments\n\n"
            f"Du {c.debut:%d/%m/%Y} au {c.fin:%d/%m/%Y}\n\n"
            "Lecture directe de BigQuery, dataset `marts`.")
        if st.button("Rafraîchir les données", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    return choix, filtres


TITRES_COURTS = ["Régime de change", "Volatilité par classe", "Exportations",
                 "Sociétés et matières", "Périodes de tension"]

try:
    index, filtres = barre_laterale()
    page = PAGES[index]
    st.title(page.TITRE)
    st.markdown(f'<div class="reponse">{page.REPONSE}</div>',
                unsafe_allow_html=True)
    page.rendre(filtres)
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()
