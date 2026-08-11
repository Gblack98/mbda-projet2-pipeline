"""Question 1 — le regime de change protege-t-il de la volatilite ?"""

import plotly.graph_objects as go
import streamlit as st

import donnees
import style as s

TITRE = "Le régime de change protège-t-il de la volatilité ?"
REPONSE = ("Oui, et l'écart est total. Les monnaies arrimées à l'euro affichent "
           "une variabilité nulle, le naira nigérian atteint 0,721.")


def rendre(filtres):
    d = donnees.devises()
    d = d[d["regime"] != "reference"].sort_values("coefficient_variation")

    xof = d[d["devise_id"] == "XOF"].iloc[0]
    ngn = d[d["devise_id"] == "NGN"].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Franc CFA · arrimé", s.nb(xof.coefficient_variation, 3),
              help="Une seule valeur distincte sur tout l'historique")
    c2.metric("Naira · flottant", s.nb(ngn.coefficient_variation, 3),
              help="La plus variable des 15 devises suivies")
    c3.metric("Devises arrimées", int((d["regime"] == "arrime").sum()))
    c4.metric("Devises suivies", len(d), help="Plus l'euro, qui sert de base")

    st.markdown("## Coefficient de variation face à l'euro")
    st.caption("Écart-type du taux divisé par sa moyenne, sur dix ans. Sans "
               "unité, donc comparable d'une devise à l'autre.")

    # --- graphique : barres horizontales, une couleur par regime ------------
    # Isselmou : c'est ici qu'on travaille la forme. Barres horizontales et
    # non verticales parce que les noms de devises se lisent alors normalement.
    fig = go.Figure()
    for regime in ["arrime", "gere", "flottant"]:
        part = d[d["regime"] == regime]
        if part.empty:
            continue
        fig.add_bar(
            y=part["devise_id"] + " · " + part["nom_devise"],
            x=part["coefficient_variation"],
            name=s.NOM_REGIME[regime],
            orientation="h",
            marker_color=s.COULEUR_REGIME[regime],
            text=[s.nb(v, 3) for v in part["coefficient_variation"]],
            textposition="outside",
            textfont=dict(color=s.ENCRE, size=12),
            hovertemplate="<b>%{y}</b><br>coefficient %{x:.4f}<extra></extra>",
        )
    fig.update_layout(barmode="stack", bargap=0.32)
    fig.update_xaxes(range=[0, float(d["coefficient_variation"].max()) * 1.18])
    st.plotly_chart(s.habiller(fig, hauteur=30 * len(d) + 90),
                    width="stretch")

    st.info("**À dire dans le rapport.** Le coefficient mesure la variabilité "
            "face à l'euro, pas une politique monétaire. Il classe le dollar et "
            "la livre en « géré » alors qu'ils flottent librement : ils sont "
            "simplement peu volatils face à l'euro.")

    with st.expander("Voir les données"):
        st.dataframe(
            d[["devise_id", "nom_devise", "coefficient_variation", "regime"]]
            .rename(columns={"devise_id": "Devise", "nom_devise": "Nom",
                             "coefficient_variation": "Coefficient",
                             "regime": "Régime"}),
            width="stretch", hide_index=True)
