"""Question 1 - Le regime de change protege-t-il de la volatilite ?

Donnees : donnees.devises(). Palette et regles de mise en forme : voir
docs/guide-dashboard.md, section 4.
"""

import os
import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import donnees  # noqa: E402

# Palette fermee du projet (.streamlit/config.toml, docs/guide-dashboard.md).
BLEU = "#2a78d6"
ORANGE = "#eb6834"
VERT = "#1baf7a"

COULEURS_REGIME = {"arrimé": BLEU, "géré": ORANGE, "flottant": VERT}
LIBELLE_REGIME = {"arrime": "arrimé", "gere": "géré", "flottant": "flottant"}


def habiller(fig, hauteur=420):
    fig.update_layout(height=hauteur, paper_bgcolor="white",
                       plot_bgcolor="white", margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f6", zeroline=False)
    return fig


st.set_page_config(page_title="Régime de change", page_icon="📊", layout="wide")

st.title("Le régime de change protège-t-il de la volatilité ?")
st.caption(
    "Les monnaies arrimées affichent une volatilité nulle, "
    "les flottantes jusqu'à 0,72.")

d = donnees.devises()
if d.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

# La ligne « reference » est l'euro : il sert de base et n'a donc pas de
# taux face à lui-même.
d = d[d["regime"] != "reference"].copy()
d["regime"] = d["regime"].map(LIBELLE_REGIME)
d = d.sort_values("coefficient_variation")
d["devise"] = d["symbole"] + " — " + d["nom_devise"]

plus_stables = d[d["coefficient_variation"] == d["coefficient_variation"].min()]
plus_volatile = d.loc[d["coefficient_variation"].idxmax()]

c1, c2, c3 = st.columns(3)
c1.metric("Arrimées (" + " et ".join(plus_stables["nom_devise"]) + ")", "0,000")
c2.metric(f"Plus volatile — {plus_volatile['nom_devise']}",
          f"{plus_volatile['coefficient_variation']:.3f}".replace(".", ","))
c3.metric("Écart entre les deux",
          f"{plus_volatile['coefficient_variation']:.3f}".replace(".", ","))

st.divider()

fig = px.bar(
    d, x="coefficient_variation", y="devise", color="regime",
    orientation="h",
    color_discrete_map=COULEURS_REGIME,
    category_orders={"regime": ["arrimé", "géré", "flottant"]},
    labels={"coefficient_variation": "Coefficient de variation", "devise": ""},
)
fig.update_traces(marker_line_width=0)
fig.update_yaxes(autorange="reversed")
st.plotly_chart(habiller(fig), width="stretch")

st.caption(
    "Le coefficient mesure la variabilité face à l'euro, pas une politique "
    "monétaire déclarée : il classe par exemple le dollar américain en "
    "« géré », alors qu'il flotte librement, simplement parce qu'il bouge "
    "peu face à l'euro.")

with st.expander("Voir les données"):
    st.dataframe(
        d[["symbole", "nom_devise", "coefficient_variation", "regime"]],
        width="stretch", hide_index=True)
