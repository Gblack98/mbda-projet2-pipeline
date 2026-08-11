"""Question 5 — quelles ont ete les periodes de tension ?"""

import plotly.graph_objects as go
import streamlit as st

import donnees
import style as s

TITRE = "Quelles ont été les périodes de tension ?"
REPONSE = ("Deux mois seulement dépassent le seuil sur dix ans, tous les deux "
           "au premier trimestre 2020. Mars est le mois du krach, avril celui "
           "du prix négatif du pétrole. Ce sont deux faits différents.")

FILTRES = ["annees", "mesure"]


def rendre(filtres):
    d = donnees.tension()
    d = d[d["annee"].between(*filtres["annees"])]
    champ = ("volatilite_hors_anomalie" if filtres["hors_anomalie"]
             else "volatilite")

    mediane = float(d["mediane_historique"].iloc[0])
    seuil = mediane * 3
    tri = d.sort_values("volatilite", ascending=False)
    pire, second = tri.iloc[0], tri.iloc[1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(str(pire.mois)[:7], s.nb(pire.volatilite, 2),
              f"{s.nb(pire.volatilite_hors_anomalie, 2)} hors anomalie",
              delta_color="off")
    c2.metric(str(second.mois)[:7], s.nb(second.volatilite, 2),
              help="Le vrai mois du krach")
    c3.metric("Médiane historique", s.nb(mediane, 2),
              help=f"Sur {len(d)} mois observés")
    c4.metric("Mois en tension", int(d["est_tension"].sum()),
              help=f"Au-delà de {s.nb(seuil, 2)}, soit trois fois la médiane")

    st.markdown("## Dispersion mensuelle des variations quotidiennes")
    st.caption("Tous instruments confondus. En rouge, les mois qui dépassent "
               "trois fois la médiane des mois observés. Le seuil est relatif "
               "aux données, il suit l'historique quand il s'allonge.")

    # --- graphique : colonnes, le rouge est un statut, pas une serie --------
    # Isselmou : le rouge est reserve a l'alerte. Ne pas s'en servir comme
    # cinquieme couleur de serie ailleurs, sinon il ne veut plus rien dire.
    couleurs = [s.ALERTE if t else s.BLEU for t in d["est_tension"]]
    fig = go.Figure()
    fig.add_bar(
        x=d["mois"], y=d[champ], marker_color=couleurs, name="volatilité",
        customdata=d[["volatilite", "volatilite_hors_anomalie",
                      "multiple_mediane"]],
        hovertemplate="<b>%{x|%B %Y}</b>"
                      "<br>toutes observations %{customdata[0]:.2f}"
                      "<br>hors anomalie %{customdata[1]:.2f}"
                      "<br>%{customdata[2]:.2f} fois la médiane<extra></extra>")
    fig.add_hline(y=seuil, line=dict(color=s.ALERTE, width=1.5, dash="solid"),
                  opacity=0.5,
                  annotation_text=f"seuil de tension {s.nb(seuil, 2)}",
                  annotation_position="top right",
                  annotation_font=dict(color=s.ALERTE, size=11))
    st.plotly_chart(s.habiller(fig, hauteur=380, legende=False),
                    width="stretch")

    gauche, droite = st.columns([1, 1])
    with gauche:
        st.markdown("## Les cinq mois les plus agités")
        cinq = tri.head(5).iloc[::-1]
        fig = go.Figure()
        fig.add_bar(y=[str(m)[:7] for m in cinq["mois"]], x=cinq["volatilite"],
                    orientation="h", name="Toutes les observations",
                    marker_color=[s.ALERTE if t else s.BLEU
                                  for t in cinq["est_tension"]],
                    text=[s.nb(v, 2) for v in cinq["volatilite"]],
                    textposition="outside", textfont=dict(color=s.ENCRE, size=11))
        fig.add_bar(y=[str(m)[:7] for m in cinq["mois"]],
                    x=cinq["volatilite_hors_anomalie"], orientation="h",
                    name="Hors anomalie", marker_color=s.GRIS,
                    text=[s.nb(v, 2) for v in cinq["volatilite_hors_anomalie"]],
                    textposition="outside", textfont=dict(color=s.ENCRE, size=11))
        fig.update_layout(barmode="group", bargap=0.3)
        fig.update_xaxes(range=[0, float(cinq["volatilite"].max()) * 1.25])
        st.plotly_chart(s.habiller(fig, hauteur=380), width="stretch")

    with droite:
        st.markdown("## Ce que dit vraiment le pic d'avril 2020")
        st.markdown(f"""
Le 20 avril 2020, le pétrole WTI a coté **-37,63 dollars** : les capacités de
stockage étaient saturées et les détenteurs de contrats payaient pour s'en
débarrasser.

La variation en pourcentage se calcule par `clôture / clôture précédente - 1`.
Quand le signe change, ce calcul n'a plus de sens : il produit **-306 %** ce
jour-là, puis **-127 %** le lendemain. Une baisse de plus de 100 % est
impossible pour un rendement.

Ces deux lignes, sur 103 104, portent à elles seules le record d'avril 2020 :
**{s.nb(pire.volatilite, 2)} avec, {s.nb(pire.volatilite_hors_anomalie, 2)}
sans**. En les écartant, avril passe derrière mars.

Le choix retenu a été de **ne rien supprimer** : une colonne
`variation_exploitable` marque ces lignes, et chaque table d'agrégation publie
les deux mesures. Masquer la valeur aurait fait disparaître un fait réel.
""")

    with st.expander("Voir les données"):
        st.dataframe(tri, width="stretch", hide_index=True)
