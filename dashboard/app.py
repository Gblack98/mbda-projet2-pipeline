"""Point d'entree du tableau de bord : menu horizontal, une page par question.

    ./venv-dashboard/bin/streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(page_title="Matières premières et devises",
                    page_icon="📊", layout="wide")

# Habillage du menu horizontal, avec la palette fermee du projet
# (docs/questions-metier.md) : soulignement bleu sur l'onglet actif,
# fond legerement teinte au survol.
st.markdown("""
<style>
[data-testid="stHeader"] {
    background-color: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
}
[data-testid="stTopNavLink"] {
    border-radius: 6px 6px 0 0;
    border-bottom: 3px solid transparent;
    margin: 0 2px;
    transition: background-color 120ms ease;
}
[data-testid="stTopNavLink"]:hover {
    background-color: #eaf1fb;
}
[data-testid="stTopNavLink"][aria-current="page"] {
    background-color: #eaf1fb;
    border-bottom: 3px solid #2a78d6;
}
[data-testid="stTopNavLink"][aria-current="page"] * {
    color: #2a78d6 !important;
    font-weight: 600;
}
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
