"""Question 4 - Les societes extractives suivent-elles leur matiere ?

Donnees : donnees.correlations() pour le classement, donnees.variations_paire()
pour les nuages. Le temoin (Orange / Or) est en gris : il ne mesure aucun lien
reel, et c'est lui qui valide que les correlations des minieres ne sont pas un
artefact de calcul.
"""

import os
import sys

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import charte  # noqa: E402
import donnees  # noqa: E402

# Six paires pour la grille : les trois minieres aurifieres de tete, une
# petroliere, une cuprifere, et le temoin. Memes echelles partout.
PAIRES_GRILLE = [
    "barrick_or", "newmont_or", "kinross_or",
    "exxon_brent", "glencore_cuivre", "orange_or",
]

st.title("Les sociétés extractives suivent-elles leur matière ?")
st.caption(
    "Oui, et le classement se lit tout seul : les minières de l'or en tête, "
    "le témoin, sans rapport avec l'or, proche de zéro.")

c = donnees.correlations()
if c.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()
c = c.sort_values("correlation", ascending=False)

st.sidebar.header("Filtres")
with st.sidebar:
    seuil = st.slider(
        "Corrélation minimale", 0.0, 0.7, 0.0, 0.05,
        help="Filtre le classement. Le témoin reste toujours affiché : "
             "c'est lui qui prouve la méthode.")

meilleure = c[~c["temoin"]].iloc[0]
temoin = c[c["temoin"]].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric(f"Plus forte · {meilleure['libelle']}",
          charte.nb(meilleure["correlation"], 3))
c2.metric(f"Témoin · {temoin['libelle']}", charte.nb(temoin["correlation"], 3),
          "doit rester proche de zéro", delta_color="off")
c3.metric("Écart avec le témoin",
          charte.nb(meilleure["correlation"] - temoin["correlation"], 3))

st.divider()

visible = c[(c["correlation"] >= seuil) | c["temoin"]]

fig = go.Figure()
for est_temoin, couleur, nom in [(False, charte.BLEU, "Paire réelle"),
                                 (True, charte.GRIS, "Témoin")]:
    d = visible[visible["temoin"] == est_temoin]
    if d.empty:
        continue
    fig.add_bar(
        y=d["libelle"], x=d["correlation"], name=nom, orientation="h",
        marker_color=couleur, marker_line_width=0,
        text=[charte.nb(v, 3) for v in d["correlation"]],
        textposition="outside", cliponaxis=False,
        customdata=d["jours_communs"],
        hovertemplate="%{y}<br>r = %{x:.3f}<br>%{customdata} séances communes"
                      "<extra>" + nom + "</extra>")

fig.update_layout(xaxis_title="Corrélation de Pearson (r)")
fig.update_yaxes(categoryorder="array",
                 categoryarray=visible["libelle"].tolist()[::-1])
fig.update_xaxes(range=[0, max(visible["correlation"].max() * 1.18, 0.1)])
st.plotly_chart(
    charte.habiller(fig, hauteur=500, grille="x", legende=True),
    width="stretch")

st.caption(
    "Le témoin, Orange face à l'or, ne mesure aucun lien réel. Sa corrélation "
    "quasi nulle est ce qui prouve que les 0,6 des minières ne sont pas un "
    "artefact de calcul. Un test dbt échoue s'il dépasse 0,15.")

st.divider()
st.subheader("Variations quotidiennes appariées")
st.caption(
    "Un point par séance. Plus les points s'alignent sur la droite, plus la "
    "société suit sa matière première. Même échelle sur les six graphiques.")

paires = {row["paire_id"]: row for _, row in c.iterrows()
          if row["paire_id"] in PAIRES_GRILLE}
retenues = [p for p in PAIRES_GRILLE if p in paires]

donnees_paires, borne = {}, 0.0
for paire_id in retenues:
    ligne = paires[paire_id]
    v = donnees.variations_paire(ligne["instrument_action"],
                                 ligne["instrument_matiere"])
    donnees_paires[paire_id] = (ligne, v)
    if not v.empty:
        borne = max(borne, v["action"].abs().max(), v["matiere"].abs().max())
borne = borne * 1.05 if borne else 1.0

t = charte.encre()
fig2 = make_subplots(
    rows=2, cols=3, horizontal_spacing=0.06, vertical_spacing=0.13,
    subplot_titles=[f"{paires[p]['libelle']} · r = "
                    f"{charte.nb(paires[p]['correlation'], 2)}"
                    for p in retenues])

for i, paire_id in enumerate(retenues):
    ligne, v = donnees_paires[paire_id]
    if v.empty:
        continue
    rang, col = divmod(i, 3)
    couleur = charte.GRIS if ligne["temoin"] else charte.BLEU
    fig2.add_scatter(
        x=v["action"], y=v["matiere"], mode="markers",
        marker=dict(size=7, color=couleur, opacity=0.45,
                    line=dict(width=0)),
        showlegend=False, row=rang + 1, col=col + 1,
        hovertemplate="action %{x:.2f} %<br>matière %{y:.2f} %<extra></extra>")
    if len(v) >= 2:
        pente, ordonnee = np.polyfit(v["action"], v["matiere"], 1)
        fig2.add_scatter(
            x=[-borne, borne],
            y=[pente * -borne + ordonnee, pente * borne + ordonnee],
            mode="lines", line=dict(width=2, color=couleur),
            showlegend=False, hoverinfo="skip", row=rang + 1, col=col + 1)
    fig2.update_xaxes(range=[-borne, borne], row=rang + 1, col=col + 1,
                      showgrid=False, linecolor=t["axe"], zeroline=True,
                      zerolinecolor=t["grille"])
    fig2.update_yaxes(range=[-borne, borne], row=rang + 1, col=col + 1,
                      showgrid=True, gridcolor=t["grille"], zeroline=True,
                      zerolinecolor=t["grille"])

for annotation in fig2.layout.annotations:
    annotation.font.size = 12
    annotation.font.color = t["texte"]

fig2.update_layout(margin=dict(l=8, r=8, t=34, b=8))
st.plotly_chart(charte.habiller(fig2, hauteur=580), width="stretch")

with st.expander("Voir les données"):
    st.dataframe(
        c[["libelle", "temoin", "jours_communs", "correlation",
           "part_variance_expliquee"]],
        width="stretch", hide_index=True)
