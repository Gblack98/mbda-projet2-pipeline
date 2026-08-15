"""Question 3 - Quel pays a le panier d'exportation le plus expose ?

Donnees : donnees.exportations() (table agg_exportations_evolution, qui porte
deja ecart_points et est_categorie_dominante). Jamais de camembert : les
categories ne totalisent pas 100 %.
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
JAUNE = "#eda100"

LIBELLE_CATEGORIE = {
    "Agricoles": "Agricoles", "Alimentaire": "Alimentaire",
    "Energie": "Énergie", "Metaux": "Métaux",
}
COULEURS_CATEGORIE = {
    "Agricoles": BLEU, "Alimentaire": ORANGE, "Énergie": VERT, "Métaux": JAUNE,
}
ORDRE_CATEGORIE = ["Agricoles", "Alimentaire", "Énergie", "Métaux"]

LIBELLE_PAYS = {
    "BEN": "Bénin", "BFA": "Burkina Faso", "CIV": "Côte d'Ivoire",
    "GHA": "Ghana", "MLI": "Mali", "MRT": "Mauritanie",
    "NGA": "Nigeria", "SEN": "Sénégal",
}


def habiller(fig, hauteur=420):
    fig.update_layout(height=hauteur, paper_bgcolor="white",
                       plot_bgcolor="white", margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f6")
    fig.update_yaxes(showgrid=False, linecolor="#e2e8f0")
    return fig


st.title("Quel pays a le panier d'exportation le plus exposé ?")
st.caption(
    "Le Nigeria dépend de l'énergie à plus de 88 % ; la Mauritanie et le "
    "Sénégal suivent, sur des matières différentes.")

e = donnees.exportations()
if e.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()
e["categorie_export"] = e["categorie_export"].map(LIBELLE_CATEGORIE)
e["pays_nom"] = e["pays"].map(LIBELLE_PAYS)

st.sidebar.header("🔧 Filtres")
annees = sorted(e["annee"].unique(), reverse=True)
annee = st.sidebar.selectbox("Année", annees, index=0)

ef = e[e["annee"] == annee]
if ef.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

dominant = ef[ef["est_categorie_dominante"]].sort_values(
    "part_exportations", ascending=False)

c1, c2, c3 = st.columns(3)
if len(dominant) >= 1:
    r = dominant.iloc[0]
    c1.metric(f"{r['pays_nom']} — {r['categorie_export']}",
              f"{r['part_exportations']:.1f} %".replace(".", ","))
if len(dominant) >= 2:
    r = dominant.iloc[1]
    c2.metric(f"{r['pays_nom']} — {r['categorie_export']}",
              f"{r['part_exportations']:.1f} %".replace(".", ","))
if len(dominant) >= 3:
    r = dominant.iloc[2]
    c3.metric(f"{r['pays_nom']} — {r['categorie_export']}",
              f"{r['part_exportations']:.1f} %".replace(".", ","))

st.divider()

ordre_pays = (ef.groupby("pays_nom")["part_exportations"].sum()
              .sort_values(ascending=False).index.tolist())

fig = go.Figure()
for categorie in ORDRE_CATEGORIE:
    d = ef[ef["categorie_export"] == categorie].set_index("pays_nom")
    d = d.reindex(ordre_pays)
    fig.add_bar(
        y=ordre_pays, x=d["part_exportations"], name=categorie,
        orientation="h", marker_color=COULEURS_CATEGORIE[categorie],
        marker_line=dict(width=2, color="white"))
fig.update_layout(
    barmode="stack", xaxis_title=f"Part des exportations en {annee} (%)",
    yaxis=dict(autorange="reversed"), legend_title="")
st.plotly_chart(habiller(fig), width="stretch")

st.caption(
    "`part_exportations` est déjà un pourcentage : un écart se lit en "
    "points, pas en pourcentage.")

st.divider()

pays_defaut = dominant.iloc[0]["pays_nom"] if len(dominant) else ordre_pays[0]
pays_choisi = st.selectbox("Évolution du panier — pays", sorted(LIBELLE_PAYS.values()),
                            index=sorted(LIBELLE_PAYS.values()).index(pays_defaut))

hist = e[e["pays_nom"] == pays_choisi].sort_values("annee")
fig2 = go.Figure()
for categorie in ORDRE_CATEGORIE:
    d = hist[hist["categorie_export"] == categorie]
    if d.empty:
        continue
    fig2.add_scatter(
        x=d["annee"], y=d["part_exportations"], mode="lines+markers",
        name=categorie, line=dict(width=2, color=COULEURS_CATEGORIE[categorie]),
        marker=dict(size=8, color=COULEURS_CATEGORIE[categorie]))
fig2.update_layout(
    xaxis_title="Année", yaxis_title="Part des exportations (%)",
    legend_title="")
fig2.update_xaxes(dtick=1)
st.plotly_chart(habiller(fig2, hauteur=340), width="stretch")

recent = hist[hist["annee"] == hist["annee"].max()]
recent = recent[recent["est_categorie_dominante"]]
if len(recent) and recent.iloc[0]["ecart_points"] == recent.iloc[0]["ecart_points"]:
    r = recent.iloc[0]
    signe = "gagne" if r["ecart_points"] >= 0 else "perd"
    points = f"{abs(r['ecart_points']):.1f}".replace(".", ",")
    st.caption(
        f"Entre {int(r['annee_precedente'])} et {int(r['annee'])}, "
        f"{r['categorie_export'].lower()} {signe} {points} points au "
        f"{pays_choisi}.")

with st.expander("Voir les données"):
    st.dataframe(
        ef[["pays_nom", "categorie_export", "part_exportations",
            "est_categorie_dominante", "ecart_points"]]
        .sort_values(["pays_nom", "categorie_export"]),
        width="stretch", hide_index=True)
