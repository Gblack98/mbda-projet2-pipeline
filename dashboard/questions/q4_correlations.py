"""Question 4 — les societes extractives suivent-elles leur matiere ?"""

import plotly.graph_objects as go
import streamlit as st

import donnees
import style as s

TITRE = "Les sociétés extractives suivent-elles leur matière première ?"
REPONSE = ("Oui. Les trois plus gros producteurs d'or occupent les trois "
           "premières places, entre 0,62 et 0,66. Le témoin Orange, qui n'a "
           "aucun lien avec l'or, reste à 0,043 : c'est lui qui valide la "
           "méthode.")


def rendre(filtres):
    d = donnees.correlations().sort_values("correlation")
    temoin = d[d["temoin"]].iloc[0]
    premier = d.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Corrélation la plus forte", s.nb(premier.correlation, 3),
              help=premier.libelle)
    c2.metric("Témoin Orange / Or", s.nb(temoin.correlation, 3),
              help="Aucun lien économique attendu")
    c3.metric("Paires comparées", len(d))
    c4.metric("Seuil d'alerte du témoin", "0,150",
              help="Un test dbt échoue si le témoin dépasse cette valeur")

    st.markdown("## Corrélation des variations quotidiennes")
    st.caption("Coefficient de Pearson entre les variations de l'action et "
               "celles de sa matière première, sur les seules séances où les "
               "deux ont coté.")

    # --- graphique : barres horizontales, le temoin en gris -----------------
    # Isselmou : la couleur porte ici une information, pas une decoration. Le
    # gris dit « cette paire ne mesure rien, elle sert de controle ».
    fig = go.Figure()
    for temoin_flag, nom, couleur in [(False, "Paire étudiée", s.BLEU),
                                      (True, "Paire témoin", s.GRIS)]:
        part = d[d["temoin"] == temoin_flag]
        if part.empty:
            continue
        fig.add_bar(
            y=part["libelle"] + part["temoin"].map({True: "  (témoin)", False: ""}),
            x=part["correlation"], name=nom, orientation="h",
            marker_color=couleur,
            text=[s.nb(v, 3) for v in part["correlation"]],
            textposition="outside", textfont=dict(color=s.ENCRE, size=12),
            customdata=part[["jours_communs", "part_variance_expliquee"]],
            hovertemplate="<b>%{y}</b><br>r = %{x:.4f}"
                          "<br>variance expliquée %{customdata[1]:.1%}"
                          "<br>%{customdata[0]} séances<extra></extra>")
    fig.update_layout(barmode="stack", bargap=0.3)
    fig.update_xaxes(range=[0, float(d["correlation"].max()) * 1.2])
    st.plotly_chart(s.habiller(fig, hauteur=30 * len(d) + 90),
                    width="stretch")

    st.markdown("## Nuage de points")
    st.caption("Variation quotidienne de l'action en abscisse, de la matière en "
               "ordonnée. Plus les points s'alignent, plus la société suit son "
               "sous-jacent.")

    choix = st.selectbox("Paire à examiner", options=list(d["paire_id"])[::-1],
                         format_func=lambda p: d[d["paire_id"] == p].iloc[0].libelle)
    ligne = d[d["paire_id"] == choix].iloc[0]
    points = donnees.variations_paire(ligne.instrument_action,
                                      ligne.instrument_matiere, borne=12)

    fig = go.Figure()
    fig.add_scatter(
        x=points["action"], y=points["matiere"], mode="markers",
        marker=dict(size=5, color=s.BLEU, opacity=0.3,
                    line=dict(width=0)),
        name="séances",
        hovertemplate="action %{x:.2f} %<br>matière %{y:.2f} %<extra></extra>")
    # droite de tendance : pente = r x (ecart-type y / ecart-type x)
    mx, my = points["action"].mean(), points["matiere"].mean()
    pente = ligne.correlation * points["matiere"].std() / points["action"].std()
    bornes = [-12, 12]
    fig.add_scatter(x=bornes, y=[my + pente * (x - mx) for x in bornes],
                    mode="lines", line=dict(color=s.ORANGE, width=2),
                    name="tendance", hoverinfo="skip")
    fig.update_xaxes(range=[-12, 12], showgrid=True, gridcolor=s.TRAIT_CLAIR)
    fig.update_yaxes(range=[-12, 12])
    st.plotly_chart(s.habiller(fig, hauteur=460), width="stretch")
    st.caption(f"**{ligne.libelle}** · r = {s.nb(ligne.correlation, 3)} · "
               f"{int(ligne.jours_communs)} séances communes")

    st.markdown("## Stabilité dans le temps")
    st.caption("Une paire solide garde un coefficient stable d'une année sur "
               "l'autre. C'est ce découpage qui a révélé que le ticker `GOLD` "
               "ne renvoyait pas Barrick mais une autre société.")

    parannee = donnees.correlations_par_annee()
    paires = st.multiselect(
        "Paires à suivre", options=sorted(parannee["paire_id"].unique()),
        default=[p for p in ["barrick_or", "kinross_or", "orange_or"]
                 if p in set(parannee["paire_id"])],
        format_func=lambda p: parannee[parannee["paire_id"] == p].iloc[0].libelle)

    fig = go.Figure()
    for i, paire in enumerate(paires):
        part = parannee[parannee["paire_id"] == paire].sort_values("annee")
        couleur = s.GRIS if part.iloc[0].temoin else s.SERIES[i % len(s.SERIES)]
        fig.add_scatter(x=part["annee"], y=part["correlation"],
                        name=part.iloc[0].libelle, mode="lines+markers",
                        line=dict(color=couleur, width=2),
                        marker=dict(size=7, line=dict(color="white", width=2)),
                        hovertemplate="%{x} : %{y:.3f}<extra>"
                                      + part.iloc[0].libelle + "</extra>")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(s.habiller(fig, hauteur=340), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe(d.sort_values("correlation", ascending=False),
                     width="stretch", hide_index=True)
