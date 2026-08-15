"""Point d'entree du tableau de bord : menu horizontal, une page par question.

    ./venv-dashboard/bin/streamlit run dashboard/app.py

Le theme se choisit dans Reglages puis Apparence. Les couleurs d'habillage du
menu sont calculees ici a partir du theme actif : en dur, le bandeau restait
clair au-dessus d'une page sombre.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import charte  # noqa: E402

st.set_page_config(page_title="Matières premières et devises",
                   page_icon="📊", layout="wide")

_sombre = charte.sombre()
_fond = "#141b24" if _sombre else "#f8fafc"
_bord = "#242c37" if _sombre else "#e2e8f0"
_survol = "#1c2733" if _sombre else "#eaf1fb"
_actif = "#6aa6e6" if _sombre else charte.BLEU

st.markdown(f"""
<style>
[data-testid="stHeader"] {{
    background-color: {_fond};
    border-bottom: 1px solid {_bord};
}}
[data-testid="stTopNavLink"] {{
    border-radius: 6px 6px 0 0;
    border-bottom: 3px solid transparent;
    margin: 0 2px;
    transition: background-color 120ms ease;
}}
[data-testid="stTopNavLink"]:hover {{
    background-color: {_survol};
}}
[data-testid="stTopNavLink"][aria-current="page"] {{
    background-color: {_survol};
    border-bottom: 3px solid {_actif};
}}
[data-testid="stTopNavLink"][aria-current="page"] * {{
    color: {_actif} !important;
    font-weight: 600;
}}
/* les chiffres cles s'alignent mieux en chiffres tabulaires */
[data-testid="stMetricValue"] {{
    font-variant-numeric: tabular-nums;
}}
</style>
""", unsafe_allow_html=True)

pages = [
    st.Page("pages/0_Connexion.py", title="Connexion", icon="🔌", default=True),
    st.Page("pages/1_Regime_de_change.py", title="Régime de change", icon="💱"),
    st.Page("pages/2_Classe_actif.py", title="Classe d'actif", icon="📈"),
    st.Page("pages/3_Exportations.py", title="Exportations", icon="🚢"),
    st.Page("pages/4_Correlations.py", title="Corrélations", icon="🔗"),
    st.Page("pages/5_Tension.py", title="Tension", icon="🌡️"),
]

st.navigation(pages, position="top").run()
