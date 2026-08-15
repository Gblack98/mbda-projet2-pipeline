"""Question 3 - Quel pays a le panier d'exportation le plus expose ?

Donnees : donnees.exportations() (table agg_exportations_evolution, qui porte
deja ecart_points et est_categorie_dominante). Jamais de camembert : les
quatre categories suivies ne totalisent pas 100 %.
"""

import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import charte  # noqa: E402
import donnees  # noqa: E402

st.title("Quel pays a le panier d'exportation le plus exposé ?")
st.caption(
    "Le Nigeria dépend de l'énergie à plus de 88 % ; la Mauritanie et le "
    "Sénégal suivent, sur des matières différentes.")

e = donnees.exportations()
if e.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()
e["categorie_export"] = e["categorie_export"].map(charte.LIBELLE_CATEGORIE)
e["pays_nom"] = e["pays"].map(charte.LIBELLE_PAYS)

st.sidebar.header("Filtres")
with st.sidebar:
    annees = sorted(e["annee"].unique(), reverse=True)
    annee = st.selectbox("Année", annees, index=0)
    categories = st.multiselect(
        "Catégorie", charte.ORDRE_CATEGORIE, default=charte.ORDRE_CATEGORIE)

ef = e[(e["annee"] == annee) & (e["categorie_export"].isin(categories))]
if ef.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

dominant = ef[ef["est_categorie_dominante"]].sort_values(
    "part_exportations", ascending=False)

for col, (_, r) in zip(st.columns(3), dominant.head(3).iterrows()):
    col.metric(f"{r['pays_nom']} · {r['categorie_export']}",
               charte.nb(r["part_exportations"], 1) + " %")

st.divider()

ordre_pays = (ef.groupby("pays_nom")["part_exportations"].sum()
              .sort_values(ascending=False).index.tolist())

fig = go.Figure()
for categorie in charte.ORDRE_CATEGORIE:
    if categorie not in categories:
        continue
    d = ef[ef["categorie_export"] == categorie].set_index("pays_nom")
    d = d.reindex(ordre_pays)
    fig.add_bar(
        y=ordre_pays, x=d["part_exportations"], name=categorie,
        orientation="h", marker_color=charte.CATEGORIE[categorie],
        # 2 px de fond entre segments : sans cela deux teintes voisines
        # se touchent et l'oeil ne voit plus la frontiere
        marker_line=dict(width=2, color=charte.encre()["fond_survol"]),
        text=[charte.nb(x, 1) if x == x and x >= 4 else ""
              for x in d["part_exportations"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        hovertemplate="%{y}<br>%{x:.1f} %<extra>" + categorie + "</extra>")

fig.update_layout(
    barmode="stack", xaxis_title=f"Part des exportations en {annee} (%)",
    yaxis=dict(autorange="reversed"))
st.plotly_chart(
    charte.habiller(fig, hauteur=430, grille="x", legende=True),
    width="stretch")

st.caption(
    "`part_exportations` est déjà un pourcentage : un écart entre deux années "
    "se lit en points, jamais en pourcentage. Les segments sous 4 % ne sont "
    "pas étiquetés, leur valeur est dans le tableau.")

st.divider()
st.subheader("Évolution du panier dans le temps")

noms = sorted(charte.LIBELLE_PAYS.values())
defaut = dominant.iloc[0]["pays_nom"] if len(dominant) else noms[0]
pays_choisi = st.selectbox("Pays", noms, index=noms.index(defaut))

hist = e[(e["pays_nom"] == pays_choisi)
         & (e["categorie_export"].isin(categories))].sort_values("annee")

fig2 = go.Figure()
for categorie in charte.ORDRE_CATEGORIE:
    d = hist[hist["categorie_export"] == categorie]
    if d.empty:
        continue
    fig2.add_scatter(
        x=d["annee"], y=d["part_exportations"], mode="lines+markers",
        name=categorie, line=dict(width=2, color=charte.CATEGORIE[categorie]),
        marker=dict(size=8, color=charte.CATEGORIE[categorie]),
        hovertemplate="%{y:.1f} %<extra>" + categorie + "</extra>")

fig2.update_layout(
    xaxis_title="Année", yaxis_title="Part des exportations (%)",
    hovermode="x unified")
fig2.update_xaxes(dtick=1)
st.plotly_chart(
    charte.habiller(fig2, hauteur=340, legende=True), width="stretch")

recent = hist[hist["annee"] == hist["annee"].max()]
recent = recent[recent["est_categorie_dominante"]]
if len(recent) and recent.iloc[0]["ecart_points"] == recent.iloc[0]["ecart_points"]:
    r = recent.iloc[0]
    signe = "gagne" if r["ecart_points"] >= 0 else "perd"
    st.caption(
        f"Entre {int(r['annee_precedente'])} et {int(r['annee'])}, "
        f"{r['categorie_export'].lower()} {signe} "
        f"{charte.nb(abs(r['ecart_points']), 1)} points au {pays_choisi}.")

with st.expander("Voir les données"):
    st.dataframe(
        ef[["pays_nom", "categorie_export", "part_exportations",
            "est_categorie_dominante", "ecart_points"]]
        .sort_values(["pays_nom", "categorie_export"]),
        width="stretch", hide_index=True)
