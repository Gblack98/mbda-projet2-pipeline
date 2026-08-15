"""Question 5 - Quelles ont ete les periodes de tension ?

Donnees : donnees.tension() (table agg_tension_mensuelle : le seuil, trois
fois la mediane historique, est deja calcule) et donnees.volatilite_classe_mois()
pour le second visuel (mars et avril 2020 par classe d'actif).
"""

import datetime
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import donnees  # noqa: E402

BLEU = "#2a78d6"
ORANGE = "#eb6834"
VERT = "#1baf7a"
ALERTE = "#e34948"

LIBELLE_CLASSE = {
    "Matieres premieres": "Matières premières", "Actions": "Actions",
    "Indices": "Indices",
}
COULEURS_CLASSE = {"Matières premières": BLEU, "Actions": ORANGE, "Indices": VERT}


def habiller(fig, hauteur=420):
    fig.update_layout(height=hauteur, paper_bgcolor="white",
                       plot_bgcolor="white", margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f6", zeroline=False)
    return fig


st.set_page_config(page_title="Tension", page_icon="📊", layout="wide")

st.title("Quelles ont été les périodes de tension ?")
st.caption(
    "Deux mois seulement dépassent le seuil, tous les deux au premier "
    "trimestre 2020.")

t = donnees.tension()
if t.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()
t["mois"] = pd.to_datetime(t["mois"])
t["annee"] = t["mois"].dt.year

st.sidebar.header("🔧 Filtres")
mesure = st.sidebar.radio(
    "Mesure", ["Avec anomalies", "Hors anomalie"],
    help="« Hors anomalie » écarte les deux séances du WTI à prix négatif, "
         "avril 2020, qui ne sont pas des rendements.")
colonne = "volatilite" if mesure == "Avec anomalies" else "volatilite_hors_anomalie"

annee_min, annee_max = int(t["annee"].min()), int(t["annee"].max())
periode = st.sidebar.slider("Période", annee_min, annee_max, (annee_min, annee_max))

tf = t[t["annee"].between(periode[0], periode[1])]
if tf.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

seuil = tf["mediane_historique"].iloc[0] * 3
nb_tension = int(tf["est_tension"].sum())
pire = tf.loc[tf[colonne].idxmax()]

c1, c2, c3 = st.columns(3)
c1.metric("Mois de tension", nb_tension)
c2.metric(f"Pire mois — {pire['mois']:%m/%Y}",
          f"{pire[colonne]:.2f}".replace(".", ","))
c3.metric("Seuil (3× la médiane)", f"{seuil:.2f}".replace(".", ","))

st.divider()

couleurs = tf["est_tension"].map({True: ALERTE, False: BLEU})
fig = go.Figure()
fig.add_bar(x=tf["mois"], y=tf[colonne], marker_color=couleurs, name=mesure)
fig.add_hline(y=seuil, line_dash="dot", line_color=ALERTE,
              annotation_text="seuil (3× médiane)", annotation_position="top left")
fig.update_layout(xaxis_title="Mois",
                   yaxis_title="Volatilité (écart-type des variations, %)")
st.plotly_chart(habiller(fig), width="stretch")

st.caption(
    "Le pic d'avril 2020 tient à deux séances sur 853, le WTI à prix "
    "négatif. Sans elles le mois retombe à 4,74 et passe derrière mars : "
    "le mois du krach est mars, celui de l'anomalie de prix est avril.")

st.divider()
st.subheader("Volatilité par classe d'actif — mars et avril 2020")

mars_avril = donnees.volatilite_classe_mois(
    [datetime.date(2020, 3, 1), datetime.date(2020, 4, 1)])
mars_avril["classe_actif"] = mars_avril["classe_actif"].map(LIBELLE_CLASSE)
mars_avril = mars_avril.sort_values(colonne, ascending=False)

fig2 = go.Figure()
fig2.add_bar(
    x=mars_avril["classe_actif"], y=mars_avril[colonne],
    marker_color=[COULEURS_CLASSE[c] for c in mars_avril["classe_actif"]],
    marker_line_width=0)
fig2.update_layout(xaxis_title="", yaxis_title="Volatilité (%)")
st.plotly_chart(habiller(fig2, hauteur=320), width="stretch")

st.caption(
    "Le classement s'inverse selon la mesure : avec les deux séances "
    "anormales, les matières premières sont la classe la plus agitée du "
    "krach ; sans elles, la plus calme.")

with st.expander("Voir les données"):
    st.dataframe(
        tf[["mois", "volatilite", "volatilite_hors_anomalie",
            "mediane_historique", "multiple_mediane", "est_tension"]],
        width="stretch", hide_index=True)
