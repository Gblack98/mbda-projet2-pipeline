"""Question 4 - Les societes extractives suivent-elles leur matiere ?

Donnees : donnees.correlations() pour le classement, donnees.variations_paire()
pour les nuages de points. Le temoin (Orange / Or) est colore en gris : il ne
mesure aucun lien reel, et sert a valider que les correlations des minieres
n'est pas un artefact de calcul.
"""

import os
import sys

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import donnees  # noqa: E402

BLEU = "#2a78d6"
GRIS = "#94a3b8"

# Six paires pour la grille de nuages : les trois premieres minieres aurifieres,
# une petroliere, une cuprifere, et le temoin. Memes echelles partout.
PAIRES_GRILLE = [
    "barrick_or", "newmont_or", "kinross_or",
    "exxon_brent", "glencore_cuivre", "orange_or",
]


def habiller(fig, hauteur=420):
    fig.update_layout(height=hauteur, paper_bgcolor="white",
                       plot_bgcolor="white", margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f6", zeroline=False)
    return fig


st.set_page_config(page_title="Corrélations", page_icon="📊", layout="wide")

st.title("Les sociétés extractives suivent-elles leur matière ?")
st.caption(
    "Oui, et le classement se lit tout seul : les minières de l'or en tête, "
    "le témoin — sans rapport avec l'or — proche de zéro.")

c = donnees.correlations()
if c.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()
c = c.sort_values("correlation", ascending=False)

meilleure = c[~c["temoin"]].iloc[0]
temoin = c[c["temoin"]].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric(f"Plus forte — {meilleure['libelle']}",
          f"{meilleure['correlation']:.3f}".replace(".", ","))
c2.metric(f"Témoin — {temoin['libelle']}",
          f"{temoin['correlation']:.3f}".replace(".", ","))
c3.metric("Écart", f"{meilleure['correlation'] - temoin['correlation']:.3f}"
          .replace(".", ","))

st.divider()

c["type"] = c["temoin"].map({True: "Témoin", False: "Paire"})
fig = go.Figure()
for type_, couleur in [("Paire", BLEU), ("Témoin", GRIS)]:
    d = c[c["type"] == type_]
    fig.add_bar(
        y=d["libelle"], x=d["correlation"], name=type_, orientation="h",
        marker_color=couleur, marker_line_width=0)
fig.update_layout(
    yaxis=dict(categoryorder="array", categoryarray=c["libelle"][::-1]),
    xaxis_title="Corrélation (r)", legend_title="")
st.plotly_chart(habiller(fig), width="stretch")

st.caption(
    "Le témoin (Orange face à l'or, sans rapport réel) reste proche de zéro : "
    "c'est ce qui prouve que les corrélations des minières ne sont pas un "
    "artefact de calcul.")

st.divider()
st.subheader("Variations quotidiennes appariées")
st.caption(
    "Un point par séance. Plus les points s'alignent, plus la société suit "
    "sa matière première. Même échelle sur les six graphiques.")

paires = {row["paire_id"]: row for _, row in c.iterrows()
          if row["paire_id"] in PAIRES_GRILLE}
donnees_paires = {}
borne = 0.0
for paire_id in PAIRES_GRILLE:
    ligne = paires.get(paire_id)
    if ligne is None:
        continue
    v = donnees.variations_paire(ligne["instrument_action"], ligne["instrument_matiere"])
    donnees_paires[paire_id] = (ligne, v)
    if not v.empty:
        borne = max(borne, v["action"].abs().max(), v["matiere"].abs().max())
borne = borne * 1.05 if borne else 1.0

fig2 = make_subplots(
    rows=2, cols=3,
    subplot_titles=[f"{paires[p]['libelle']} (r={paires[p]['correlation']:.2f})"
                     for p in PAIRES_GRILLE if p in paires])

for i, paire_id in enumerate(PAIRES_GRILLE):
    if paire_id not in donnees_paires:
        continue
    ligne, v = donnees_paires[paire_id]
    row, col = divmod(i, 3)
    couleur = GRIS if ligne["temoin"] else BLEU
    if v.empty:
        continue
    fig2.add_scatter(
        x=v["action"], y=v["matiere"], mode="markers",
        marker=dict(size=8, color=couleur, opacity=0.6),
        showlegend=False, row=row + 1, col=col + 1)
    if len(v) >= 2:
        pente, ordonnee = np.polyfit(v["action"], v["matiere"], 1)
        xs = [-borne, borne]
        fig2.add_scatter(
            x=xs, y=[pente * x + ordonnee for x in xs], mode="lines",
            line=dict(width=2, color=couleur), showlegend=False,
            row=row + 1, col=col + 1)
    fig2.update_xaxes(range=[-borne, borne], row=row + 1, col=col + 1,
                       showgrid=False, linecolor="#e2e8f0", zeroline=True,
                       zerolinecolor="#e2e8f0")
    fig2.update_yaxes(range=[-borne, borne], row=row + 1, col=col + 1,
                       showgrid=True, gridcolor="#eef2f6", zeroline=True,
                       zerolinecolor="#e2e8f0")

fig2.update_layout(height=560, paper_bgcolor="white", plot_bgcolor="white",
                    margin=dict(l=8, r=8, t=40, b=8))
st.plotly_chart(fig2, width="stretch")

with st.expander("Voir les données"):
    st.dataframe(
        c[["libelle", "temoin", "jours_communs", "correlation",
           "part_variance_expliquee"]],
        width="stretch", hide_index=True)
