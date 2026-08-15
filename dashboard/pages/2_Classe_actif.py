"""Question 2 - Quelle classe d'actif est la plus volatile ?

Donnees : donnees.volatilite_classe() pour l'evolution, donnees.volatilite_totale()
pour les chiffres d'ensemble (un ecart-type ne se moyenne pas). Palette et
mapping classe -> couleur : docs/questions-metier.md, section 2.
"""

import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import donnees  # noqa: E402

BLEU = "#2a78d6"
ORANGE = "#eb6834"
VERT = "#1baf7a"

LIBELLE_CLASSE = {
    "Matieres premieres": "Matières premières",
    "Actions": "Actions",
    "Indices": "Indices",
}
COULEURS_CLASSE = {
    "Matières premières": BLEU,
    "Actions": ORANGE,
    "Indices": VERT,
}
ORDRE_CLASSE = ["Matières premières", "Actions", "Indices"]


def habiller(fig, hauteur=420):
    fig.update_layout(height=hauteur, paper_bgcolor="white",
                       plot_bgcolor="white", margin=dict(l=8, r=90, t=8, b=8))
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f6", zeroline=False)
    return fig


st.set_page_config(page_title="Classe d'actif", page_icon="📊", layout="wide")

st.title("Quelle classe d'actif est la plus volatile ?")
st.caption(
    "Sur l'ensemble de la période, ce sont les indices, portés par le VIX. "
    "En 2020 seulement, ce sont pourtant les matières premières qui dominent.")

v = donnees.volatilite_classe()
if v.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()
v["classe_actif"] = v["classe_actif"].map(LIBELLE_CLASSE)

st.sidebar.header("🔧 Filtres")
mesure = st.sidebar.radio(
    "Mesure", ["Avec anomalies", "Hors anomalie"],
    help="« Hors anomalie » écarte les variations calculées sur une clôture "
         "négative (WTI, 20 avril 2020), qui ne sont pas des rendements.")
colonne = "volatilite" if mesure == "Avec anomalies" else "volatilite_hors_anomalie"

classes = st.sidebar.multiselect("Classe d'actif", ORDRE_CLASSE, default=ORDRE_CLASSE)

annee_min, annee_max = int(v["annee"].min()), int(v["annee"].max())
periode = st.sidebar.slider("Période", annee_min, annee_max, (annee_min, annee_max))

vf = v[v["classe_actif"].isin(classes)
       & v["annee"].between(periode[0], periode[1])]

if vf.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

# Chiffres d'ensemble : recalcules sur toutes les observations, pas la
# moyenne des annees (un ecart-type ne se moyenne pas).
vt = donnees.volatilite_totale()
vt["classe_actif"] = vt["classe_actif"].map(LIBELLE_CLASSE)
vt = vt[vt["classe_actif"].isin(classes)].sort_values(colonne, ascending=False)

cols = st.columns(len(vt)) if len(vt) else [st]
for col, (_, row) in zip(cols, vt.iterrows()):
    col.metric(f"{row['classe_actif']} (ensemble)",
               f"{row[colonne]:.2f}".replace(".", ","))

st.divider()

fig = go.Figure()
for classe in ORDRE_CLASSE:
    if classe not in classes:
        continue
    d = vf[vf["classe_actif"] == classe].sort_values("annee")
    if d.empty:
        continue
    fig.add_scatter(
        x=d["annee"], y=d[colonne], mode="lines+markers", name=classe,
        line=dict(width=2, color=COULEURS_CLASSE[classe]),
        marker=dict(size=8, color=COULEURS_CLASSE[classe]),
        showlegend=False)
    dernier = d.iloc[-1]
    fig.add_annotation(
        x=dernier["annee"], y=dernier[colonne], text=classe,
        xanchor="left", yanchor="middle", xshift=8, showarrow=False,
        font=dict(color=COULEURS_CLASSE[classe], size=13))

fig.update_layout(
    xaxis_title="Année",
    yaxis_title="Volatilité (écart-type des variations quotidiennes, %)")
fig.update_xaxes(dtick=1)
st.plotly_chart(habiller(fig), width="stretch")

st.caption(
    "En 2020, les matières premières atteignent 5,21 avec toutes les "
    "observations, mais deux séances sur 5 819 — le WTI à prix négatif le "
    "20 avril — portent tout l'écart : sans elles la classe retombe à 2,88 "
    "et passe dernière. Basculer « Mesure » pour voir la courbe s'effondrer.")

with st.expander("Voir les données"):
    st.dataframe(
        vf[["classe_actif", "annee", "volatilite", "volatilite_hors_anomalie",
            "instruments", "observations", "observations_ecartees"]]
        .sort_values(["classe_actif", "annee"]),
        width="stretch", hide_index=True)
