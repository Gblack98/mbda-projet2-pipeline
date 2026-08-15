"""Question 2 - Quelle classe d'actif est la plus volatile ?

Donnees : donnees.volatilite_classe() pour l'evolution, donnees.volatilite_totale()
pour les chiffres d'ensemble (un ecart-type ne se moyenne pas, il se recalcule
sur toutes les observations).
"""

import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import charte  # noqa: E402
import donnees  # noqa: E402

st.title("Quelle classe d'actif est la plus volatile ?")
st.caption(
    "Sur l'ensemble de la période, ce sont les indices, portés par le VIX. "
    "En 2020 seulement, ce sont pourtant les matières premières qui dominent.")

v = donnees.volatilite_classe()
if v.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()
v["classe_actif"] = v["classe_actif"].map(charte.LIBELLE_CLASSE)

st.sidebar.header("Filtres")
with st.sidebar:
    colonne, mention = charte.mesure_choisie(
        "« Hors anomalie » écarte les variations calculées sur une clôture "
        "négative (WTI, 20 avril 2020), qui ne sont pas des rendements.")
    classes = st.multiselect(
        "Classe d'actif", charte.ORDRE_CLASSE, default=charte.ORDRE_CLASSE)
    annee_min, annee_max = int(v["annee"].min()), int(v["annee"].max())
    periode = st.slider("Période", annee_min, annee_max, (annee_min, annee_max))

vf = v[v["classe_actif"].isin(classes)
       & v["annee"].between(periode[0], periode[1])]
if vf.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

# Chiffres d'ensemble : recalcules sur toutes les observations, pas la
# moyenne des annees.
vt = donnees.volatilite_totale()
vt["classe_actif"] = vt["classe_actif"].map(charte.LIBELLE_CLASSE)
vt = vt[vt["classe_actif"].isin(classes)].sort_values(colonne, ascending=False)

for col, (_, row) in zip(st.columns(max(len(vt), 1)), vt.iterrows()):
    ecart = row["volatilite"] - row["volatilite_hors_anomalie"]
    col.metric(
        f"{row['classe_actif']} · ensemble", charte.nb(row[colonne]),
        f"{charte.nb(ecart)} porté par l'anomalie" if ecart > 0.01 else None,
        delta_color="off")

st.divider()

fig = go.Figure()
for classe in charte.ORDRE_CLASSE:
    if classe not in classes:
        continue
    d = vf[vf["classe_actif"] == classe].sort_values("annee")
    if d.empty:
        continue
    fig.add_scatter(
        x=d["annee"], y=d[colonne], mode="lines+markers", name=classe,
        line=dict(width=2, color=charte.CLASSE[classe]),
        marker=dict(size=8, color=charte.CLASSE[classe]),
        hovertemplate="%{y:.2f}<extra>" + classe + "</extra>")
    # etiquette directe en bout de courbe, plus lisible qu'une legende
    dernier = d.iloc[-1]
    fig.add_annotation(
        x=dernier["annee"], y=dernier[colonne], text=classe,
        xanchor="left", yanchor="middle", xshift=10, showarrow=False,
        font=dict(color=charte.CLASSE[classe], size=13))

fig.update_layout(
    xaxis_title="Année",
    yaxis_title="Écart-type des variations quotidiennes (%)",
    hovermode="x unified")
fig.update_xaxes(dtick=1)
st.plotly_chart(
    charte.habiller(fig, hauteur=440, marge_droite=110), width="stretch")

st.caption(
    f"Mesure affichée : {mention}. En 2020, les matières premières atteignent "
    "5,21 avec toutes les observations, mais deux séances sur 5 819, le WTI à "
    "prix négatif le 20 avril, portent tout l'écart : sans elles la classe "
    "retombe à 2,88 et passe dernière. Bascule « Mesure » pour le voir.")

with st.expander("Voir les données"):
    st.dataframe(
        vf[["classe_actif", "annee", "volatilite", "volatilite_hors_anomalie",
            "instruments", "observations", "observations_ecartees"]]
        .sort_values(["classe_actif", "annee"]),
        width="stretch", hide_index=True)
