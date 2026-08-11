"""Question 2 — quelle classe d'actif est la plus volatile ?"""

import plotly.graph_objects as go
import streamlit as st

import donnees
import style as s

TITRE = "Quelle classe d'actif est la plus volatile ?"
REPONSE = ("Les indices, à 3,98, parce que le VIX en fait partie. Le VIX est "
           "l'indice de la volatilité elle-même : sans lui, les indices "
           "seraient les plus calmes des trois classes.")

FILTRES = ["annees", "classes", "mesure"]


def rendre(filtres):
    champ = ("volatilite_hors_anomalie" if filtres["hors_anomalie"]
             else "volatilite")

    total = donnees.volatilite_totale()
    total = total[total["classe_actif"].isin(filtres["classes"])]

    colonnes = st.columns(max(1, len(total)))
    for col, (_, ligne) in zip(colonnes, total.sort_values(champ, ascending=False)
                               .iterrows()):
        col.metric(s.NOM_CLASSE.get(ligne.classe_actif, ligne.classe_actif),
                   s.nb(ligne[champ], 2),
                   help=f"{int(ligne.instruments)} instruments, sur dix ans")

    if not filtres["hors_anomalie"]:
        st.warning(
            "**Lecture de l'année 2020.** Les matières premières y sont à 5,21, "
            "devant les indices et les actions. Mais deux observations sur 5 819 "
            "portent tout l'écart, les deux séances du pétrole WTI à prix "
            "négatif. Basculer la mesure sur « hors anomalie » dans le volet de "
            "gauche : la classe retombe à 2,88 et passe dernière.")

    st.markdown("## Volatilité annuelle par classe d'actif")
    st.caption("Écart-type des variations quotidiennes, année par année. "
               + ("Les variations calculées à cheval sur un changement de signe "
                  "du prix sont écartées." if filtres["hors_anomalie"]
                  else "Toutes les observations sont incluses."))

    d = donnees.volatilite_classe()
    d = d[d["classe_actif"].isin(filtres["classes"])
          & d["annee"].between(*filtres["annees"])]

    # --- graphique : une courbe par classe ---------------------------------
    # Isselmou : ajouter les points sur les courbes aide beaucoup a la lecture,
    # c'est le mode "lines+markers". Ne pas mettre d'etiquette sur chaque point,
    # ca devient illisible : l'infobulle suffit.
    fig = go.Figure()
    for classe in sorted(d["classe_actif"].unique()):
        part = d[d["classe_actif"] == classe].sort_values("annee")
        fig.add_scatter(
            x=part["annee"], y=part[champ],
            name=s.NOM_CLASSE.get(classe, classe),
            mode="lines+markers",
            line=dict(color=s.COULEUR_CLASSE.get(classe, s.GRIS), width=2),
            marker=dict(size=8, line=dict(color="white", width=2)),
            hovertemplate="<b>%{fullData.name}</b><br>%{x} : %{y:.2f}<extra></extra>",
        )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(s.habiller(fig, hauteur=420), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe(d, width="stretch", hide_index=True)
