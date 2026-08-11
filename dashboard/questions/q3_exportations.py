"""Question 3 — quel pays a le panier d'exportation le plus expose ?"""

import plotly.graph_objects as go
import streamlit as st

import donnees
import style as s

TITRE = "Quel pays a le panier d'exportation le plus exposé ?"
REPONSE = ("Le Nigeria, et de très loin : 88,6 % de ses exportations sont de "
           "l'énergie en 2024. La Mauritanie dépend des métaux à 33,7 %, le "
           "Sénégal de l'énergie à 32,7 % depuis la mise en production du champ "
           "de Sangomar.")

FILTRES = ["annee_export"]

CATEGORIES = ["Energie", "Metaux", "Alimentaire", "Agricoles"]


def rendre(filtres):
    d = donnees.exportations()
    annee = filtres["annee_export"]
    courant = d[d["annee"] == annee]

    dominantes = (courant[courant["est_categorie_dominante"]]
                  .sort_values("part_exportations", ascending=False))
    for col, (_, l) in zip(st.columns(4), dominantes.head(4).iterrows()):
        ecart = ("" if l.ecart_points is None or l.ecart_points != l.ecart_points
                 else f"{l.ecart_points:+.1f} pt")
        col.metric(s.NOM_PAYS.get(l.pays, l.pays),
                   f"{s.nb(l.part_exportations, 1)} %",
                   ecart or None,
                   help=f"Catégorie dominante : {l.categorie_export}")

    st.markdown(f"## Composition du panier d'exportation · {annee}")
    st.caption("Part de chaque catégorie dans les exportations de marchandises. "
               "Le total ne fait pas 100 % : les quatre catégories ne couvrent "
               "pas tout. Ne jamais représenter ces données en camembert.")

    # --- graphique : barres empilees horizontales ---------------------------
    # Isselmou : l'ordre des pays est celui du total, du plus expose au moins
    # expose. C'est ce tri qui fait la lecture, sans lui le graphique ne dit
    # plus rien.
    ordre = (courant.groupby("pays")["part_exportations"].sum()
             .sort_values().index.tolist())
    fig = go.Figure()
    for categorie in CATEGORIES:
        part = (courant[courant["categorie_export"] == categorie]
                .set_index("pays").reindex(ordre))
        fig.add_bar(
            y=[s.NOM_PAYS.get(p, p) for p in ordre],
            x=part["part_exportations"],
            name=s.NOM_CATEGORIE[categorie],
            orientation="h",
            marker_color=s.COULEUR_CATEGORIE[categorie],
            hovertemplate="<b>%{y}</b><br>" + s.NOM_CATEGORIE[categorie]
                          + " : %{x:.1f} %<extra></extra>",
        )
    fig.update_layout(barmode="stack", bargap=0.34)
    st.plotly_chart(s.habiller(fig, hauteur=42 * len(ordre) + 110),
                    width="stretch")

    st.markdown("## Évolution dans le temps")
    st.caption("`part_exportations` est déjà un pourcentage : un écart se lit "
               "**en points**, pas en pourcentage. Écrire « l'énergie gagne "
               "13 points » et non « gagne 13 % ».")

    pays_suivis = st.multiselect(
        "Pays à comparer", options=sorted(d["pays"].unique()),
        default=["SEN", "MRT", "NGA"],
        format_func=lambda p: s.NOM_PAYS.get(p, p))

    for pays in pays_suivis:
        fig = go.Figure()
        for categorie in CATEGORIES:
            part = d[(d["pays"] == pays)
                     & (d["categorie_export"] == categorie)].sort_values("annee")
            if part.empty:
                continue
            fig.add_scatter(
                x=part["annee"], y=part["part_exportations"],
                name=s.NOM_CATEGORIE[categorie], mode="lines+markers",
                line=dict(color=s.COULEUR_CATEGORIE[categorie], width=2),
                marker=dict(size=7, line=dict(color="white", width=2)),
                hovertemplate="%{x} : %{y:.1f} %<extra>"
                              + s.NOM_CATEGORIE[categorie] + "</extra>")
        fig.update_layout(hovermode="x unified")
        st.markdown(f"**{s.NOM_PAYS.get(pays, pays)}**")
        st.plotly_chart(s.habiller(fig, hauteur=300), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe(courant, width="stretch", hide_index=True)
