"""Palette, libelles et habillage communs aux cinq pages.

Chaque page portait sa propre fonction habiller() et sa propre liste de
couleurs. Elles avaient deja commence a diverger : marges differentes, grille
sur l'axe X ici et sur l'axe Y la. Tout est regroupe ici.

Les couleurs viennent de docs/questions-metier.md. Elles ont ete verifiees
pour le daltonisme : ne pas les changer sans revalider. Le vert et le jaune
passent sous 3:1 de contraste, d'ou la regle d'ecrire toujours la valeur
plutot que de la faire deviner par la couleur.
"""

import streamlit as st

BLEU = "#2a78d6"
ORANGE = "#eb6834"
VERT = "#1baf7a"
JAUNE = "#eda100"
GRIS = "#94a3b8"
ALERTE = "#e34948"

SERIE = [BLEU, ORANGE, VERT, JAUNE]

REGIME = {"arrimé": BLEU, "géré": JAUNE, "flottant": ORANGE}
LIBELLE_REGIME = {"arrime": "arrimé", "gere": "géré", "flottant": "flottant"}
ORDRE_REGIME = ["arrimé", "géré", "flottant"]

CLASSE = {"Matières premières": BLEU, "Actions": ORANGE, "Indices": VERT}
LIBELLE_CLASSE = {
    "Matieres premieres": "Matières premières",
    "Actions": "Actions",
    "Indices": "Indices",
}
ORDRE_CLASSE = ["Matières premières", "Actions", "Indices"]

CATEGORIE = {
    "Agricoles": BLEU, "Alimentaire": ORANGE, "Énergie": VERT, "Métaux": JAUNE,
}
LIBELLE_CATEGORIE = {
    "Agricoles": "Agricoles", "Alimentaire": "Alimentaire",
    "Energie": "Énergie", "Metaux": "Métaux",
}
ORDRE_CATEGORIE = ["Agricoles", "Alimentaire", "Énergie", "Métaux"]

LIBELLE_PAYS = {
    "BEN": "Bénin", "BFA": "Burkina Faso", "CIV": "Côte d'Ivoire",
    "GHA": "Ghana", "MLI": "Mali", "MRT": "Mauritanie",
    "NGA": "Nigeria", "SEN": "Sénégal",
}


def sombre():
    """Vrai si le lecteur a choisi le theme sombre dans Streamlit."""
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def encre():
    """Les couleurs de rendu qui dependent du theme, et elles seules.

    Les quatre couleurs de serie ne bougent jamais : une teinte suit une
    entite, quel que soit le fond.
    """
    if sombre():
        return {"texte": "#e6e9ef", "attenue": "#98a2b3",
                "grille": "#2b323d", "axe": "#39414d", "fond_survol": "#1c2430"}
    return {"texte": "#1a1a19", "attenue": "#5a6b64",
            "grille": "#eef2f6", "axe": "#e2e8f0", "fond_survol": "#ffffff"}


def habiller(fig, hauteur=420, grille="y", marge_droite=8, legende=False):
    """Reglages appliques a tous les graphiques.

    Les fonds sont transparents : c'est ce qui laisse passer le fond de
    Streamlit et fait suivre le theme au graphique. Un fond blanc en dur
    laissait une dalle claire au milieu d'une page sombre.
    """
    t = encre()
    fig.update_layout(
        height=hauteur,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=marge_droite, t=8, b=8),
        font=dict(color=t["texte"], size=13),
        hoverlabel=dict(bgcolor=t["fond_survol"], font_size=13,
                        bordercolor=t["axe"]),
        showlegend=legende,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title_text=""),
    )
    fig.update_xaxes(showgrid="x" in grille, gridcolor=t["grille"],
                     linecolor=t["axe"], zeroline=False,
                     title_font=dict(color=t["attenue"], size=12))
    fig.update_yaxes(showgrid="y" in grille, gridcolor=t["grille"],
                     linecolor=t["axe"], zeroline=False,
                     title_font=dict(color=t["attenue"], size=12))
    return fig


def nb(valeur, decimales=2):
    """Format francais : la virgule comme separateur decimal."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def mesure_choisie(aide):
    """Le selecteur « avec ou sans l'anomalie », identique sur les trois pages.

    Rend le nom de la colonne a lire et le libelle a citer sous le graphique.
    Le classement s'inverse selon la colonne : il faut toujours dire laquelle
    est affichee.
    """
    choix = st.segmented_control(
        "Mesure", ["Avec anomalies", "Hors anomalie"],
        default="Avec anomalies", help=aide)
    if choix == "Hors anomalie":
        return "volatilite_hors_anomalie", "hors anomalie de prix"
    return "volatilite", "toutes observations"
