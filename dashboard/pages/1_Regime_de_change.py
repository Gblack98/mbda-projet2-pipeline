"""Question 1 - Le regime de change protege-t-il de la volatilite ?

Donnees : donnees.devises(). Palette et mapping regime -> couleur dans
charte.py, qui vient de docs/questions-metier.md, section 1.
"""

import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import charte  # noqa: E402
import donnees  # noqa: E402

st.title("Le régime de change protège-t-il de la volatilité ?")
st.caption(
    "Les monnaies arrimées affichent une volatilité nulle, "
    "les flottantes jusqu'à 0,72.")

d = donnees.devises()
if d.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()

# La ligne « reference » est l'euro : il sert de base et n'a donc pas de
# taux face a lui-meme.
d = d[d["regime"] != "reference"].copy()
d["regime"] = d["regime"].map(charte.LIBELLE_REGIME)
d = d.sort_values("coefficient_variation")
d["devise"] = d["symbole"] + " · " + d["nom_devise"]

st.sidebar.header("Filtres")
regimes = st.sidebar.multiselect(
    "Régime", charte.ORDRE_REGIME, default=charte.ORDRE_REGIME,
    help="Le régime est déduit de la variabilité du taux, il n'est pas déclaré.")
d = d[d["regime"].isin(regimes)]

if d.empty:
    st.warning("Aucune devise pour cette sélection.")
    st.stop()

plus_stables = d[d["coefficient_variation"] == d["coefficient_variation"].min()]
plus_volatile = d.loc[d["coefficient_variation"].idxmax()]

c1, c2, c3 = st.columns(3)
c1.metric("Plus stables",
          charte.nb(plus_stables["coefficient_variation"].iloc[0], 3),
          " et ".join(plus_stables["devise_id"].head(3)), delta_color="off")
c2.metric("Plus volatile", charte.nb(plus_volatile["coefficient_variation"], 3),
          plus_volatile["devise_id"], delta_color="off")
c3.metric("Devises suivies", len(d),
          f"{d['regime'].nunique()} régimes", delta_color="off")

st.divider()

fig = go.Figure()
for regime in charte.ORDRE_REGIME:
    part = d[d["regime"] == regime]
    if part.empty:
        continue
    fig.add_bar(
        y=part["devise"], x=part["coefficient_variation"], name=regime,
        orientation="h", marker_color=charte.REGIME[regime],
        marker_line_width=0,
        text=[charte.nb(v, 3) for v in part["coefficient_variation"]],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>coefficient %{x:.3f}<extra>" + regime + "</extra>")

fig.update_layout(xaxis_title="Coefficient de variation face à l'euro")
fig.update_yaxes(
    categoryorder="array", categoryarray=d["devise"].tolist()[::-1])
# de la marge a droite, sinon l'etiquette de la plus longue barre est coupee
fig.update_xaxes(range=[0, d["coefficient_variation"].max() * 1.18])
st.plotly_chart(
    charte.habiller(fig, hauteur=460, grille="x", legende=True),
    width="stretch")

st.caption(
    "Le coefficient mesure la variabilité face à l'euro, pas une politique "
    "monétaire déclarée : il classe par exemple le dollar américain en "
    "« géré », alors qu'il flotte librement, simplement parce qu'il bouge "
    "peu face à l'euro.")

with st.expander("Voir les données"):
    st.dataframe(
        d[["symbole", "nom_devise", "coefficient_variation", "regime"]],
        width="stretch", hide_index=True)
