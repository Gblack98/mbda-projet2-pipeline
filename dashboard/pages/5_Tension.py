"""Question 5 - Quelles ont ete les periodes de tension ?

Donnees : donnees.tension() (le seuil, trois fois la mediane historique, est
deja calcule) et donnees.volatilite_classe_mois() pour le second visuel.
"""

import datetime
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import charte  # noqa: E402
import donnees  # noqa: E402

st.title("Quelles ont été les périodes de tension ?")
st.caption(
    "Deux mois seulement dépassent le seuil, tous les deux au premier "
    "trimestre 2020.")

t = donnees.tension()
if t.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()
t["mois"] = pd.to_datetime(t["mois"])
t["annee"] = t["mois"].dt.year

st.sidebar.header("Filtres")
with st.sidebar:
    colonne, mention = charte.mesure_choisie(
        "« Hors anomalie » écarte les deux séances du WTI à prix négatif, "
        "avril 2020, qui ne sont pas des rendements.")
    annee_min, annee_max = int(t["annee"].min()), int(t["annee"].max())
    periode = st.slider("Période", annee_min, annee_max, (annee_min, annee_max))

tf = t[t["annee"].between(periode[0], periode[1])]
if tf.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

seuil = tf["mediane_historique"].iloc[0] * 3
pire = tf.loc[tf[colonne].idxmax()]

c1, c2, c3 = st.columns(3)
c1.metric("Mois sous tension", int(tf["est_tension"].sum()),
          f"sur {len(tf)} mois observés", delta_color="off")
c2.metric(f"Mois le plus agité · {pire['mois']:%m/%Y}",
          charte.nb(pire[colonne]))
c3.metric("Seuil de tension", charte.nb(seuil),
          "3 fois la médiane", delta_color="off")

st.divider()

couleurs = tf["est_tension"].map({True: charte.ALERTE, False: charte.BLEU})

fig = go.Figure()
fig.add_bar(
    x=tf["mois"], y=tf[colonne], marker_color=couleurs, marker_line_width=0,
    customdata=tf["multiple_mediane"],
    hovertemplate="%{x|%m/%Y}<br>volatilité %{y:.2f}"
                  "<br>%{customdata:.1f} fois la médiane<extra></extra>")
fig.add_hline(
    y=seuil, line_dash="dot", line_color=charte.ALERTE,
    annotation_text="seuil, 3 fois la médiane", annotation_position="top left",
    annotation_font=dict(color=charte.ALERTE, size=12))
fig.update_layout(
    xaxis_title="Mois",
    yaxis_title="Écart-type des variations quotidiennes (%)")
st.plotly_chart(charte.habiller(fig, hauteur=430), width="stretch")

st.caption(
    f"Mesure affichée : {mention}. Le pic d'avril 2020 tient à deux séances "
    "sur 853, le WTI à prix négatif. Sans elles le mois retombe à 4,74 et "
    "passe derrière mars : le mois du krach est mars, celui de l'anomalie de "
    "prix est avril. Ce ne sont pas les mêmes faits.")

st.divider()
st.subheader("Volatilité par classe d'actif, mars et avril 2020")

mars_avril = donnees.volatilite_classe_mois(
    [datetime.date(2020, 3, 1), datetime.date(2020, 4, 1)])
mars_avril["classe_actif"] = mars_avril["classe_actif"].map(
    charte.LIBELLE_CLASSE)
mars_avril = mars_avril.sort_values(colonne, ascending=False)

fig2 = go.Figure()
fig2.add_bar(
    x=mars_avril["classe_actif"], y=mars_avril[colonne],
    marker_color=[charte.CLASSE[c] for c in mars_avril["classe_actif"]],
    marker_line_width=0,
    text=[charte.nb(v) for v in mars_avril[colonne]],
    textposition="outside", cliponaxis=False,
    hovertemplate="%{x}<br>volatilité %{y:.2f}<extra></extra>")
fig2.update_layout(xaxis_title="", yaxis_title="Volatilité (%)")
fig2.update_yaxes(range=[0, mars_avril[colonne].max() * 1.18])
st.plotly_chart(charte.habiller(fig2, hauteur=330), width="stretch")

st.caption(
    "Le classement s'inverse selon la mesure : avec les deux séances "
    "anormales, les matières premières sont la classe la plus agitée du "
    "krach ; sans elles, la plus calme. D'où l'obligation de dire laquelle "
    "des deux colonnes est affichée.")

with st.expander("Voir les données"):
    st.dataframe(
        tf[["mois", "volatilite", "volatilite_hors_anomalie",
            "mediane_historique", "multiple_mediane", "est_tension"]]
        .sort_values(colonne, ascending=False),
        width="stretch", hide_index=True)
