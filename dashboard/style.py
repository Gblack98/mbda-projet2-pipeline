"""Palette et reglages communs a tous les graphiques.

La palette a ete verifiee pour le daltonisme. Ne pas la changer sans revalider :
le vert et le jaune ont deja un contraste faible sur fond blanc, c'est pour ca
qu'on affiche toujours la valeur en etiquette a cote des barres.

Regle a tenir : une couleur suit une entite, jamais un rang. Si un filtre retire
une serie, les autres gardent leur teinte.
"""

BLEU = "#2a78d6"
ORANGE = "#eb6834"
VERT = "#1baf7a"
JAUNE = "#eda100"
GRIS = "#94a3b8"
ALERTE = "#e34948"  # reserve aux periodes de tension, jamais une serie

SERIES = [BLEU, ORANGE, VERT, JAUNE]

ENCRE = "#1a1a19"
ENCRE2 = "#5a6b64"
ENCRE3 = "#93a29c"
TRAIT = "#e2e8f0"
TRAIT_CLAIR = "#eef2f6"

COULEUR_REGIME = {"arrime": BLEU, "gere": JAUNE, "flottant": ORANGE,
                  "reference": GRIS}
NOM_REGIME = {"arrime": "Arrimé", "gere": "Géré", "flottant": "Flottant",
              "reference": "Référence"}

COULEUR_CLASSE = {"Indices": VERT, "Matieres premieres": BLEU, "Actions": ORANGE}
NOM_CLASSE = {"Indices": "Indices", "Matieres premieres": "Matières premières",
              "Actions": "Actions"}

COULEUR_CATEGORIE = {"Energie": BLEU, "Metaux": ORANGE, "Alimentaire": VERT,
                     "Agricoles": JAUNE}
NOM_CATEGORIE = {"Energie": "Énergie", "Metaux": "Métaux",
                 "Alimentaire": "Alimentaire", "Agricoles": "Agricoles"}

NOM_PAYS = {"SEN": "Sénégal", "MRT": "Mauritanie", "NGA": "Nigeria",
            "GHA": "Ghana", "CIV": "Côte d'Ivoire", "MLI": "Mali",
            "BFA": "Burkina Faso", "BEN": "Bénin"}


def habiller(fig, hauteur=380, legende=True):
    """Reglages communs a tous les graphiques Plotly.

    Fond blanc, grille en gris tres clair, pas de titre d'axe superflu, legende
    en haut a gauche. Appeler cette fonction sur chaque figure : c'est ce qui
    fait que les cinq pages se ressemblent.
    """
    fig.update_layout(
        height=hauteur,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif",
                  size=13, color=ENCRE2),
        hoverlabel=dict(bgcolor="#1f2937", font_color="white",
                        bordercolor="#1f2937"),
        showlegend=legende,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title_text=""),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=TRAIT,
                     tickfont=dict(color=ENCRE3, size=11), title_text="")
    fig.update_yaxes(showgrid=True, gridcolor=TRAIT_CLAIR, gridwidth=1,
                     zeroline=False, linecolor=TRAIT,
                     tickfont=dict(color=ENCRE3, size=11), title_text="")
    return fig


def nb(valeur, decimales=2):
    """Nombre a la francaise : virgule decimale, espace pour les milliers."""
    if valeur is None:
        return "—"
    texte = f"{valeur:,.{decimales}f}"
    return texte.replace(",", " ").replace(".", ",")


CSS = """
<style>
  .block-container { padding-top: 2.2rem; max-width: 1500px; }
  h1 { font-size: 1.5rem !important; font-weight: 650; letter-spacing: -.02em; }
  h2 { font-size: 1.05rem !important; font-weight: 650; padding-top: .4rem; }
  .reponse { font-size: 1rem; color: #5a6b64; margin: -.4rem 0 1.1rem;
             max-width: 80ch; line-height: 1.5; }
  div[data-testid="stMetric"] { background: #fff; border: 1px solid #e2e8f0;
             border-radius: 10px; padding: 14px 16px; }
  div[data-testid="stMetricLabel"] { font-size: .72rem !important;
             text-transform: uppercase; letter-spacing: .04em; color: #5a6b64; }
  div[data-testid="stMetricValue"] { font-size: 1.85rem; letter-spacing: -.03em; }
  section[data-testid="stSidebar"] { border-right: 1px solid #e2e8f0; }
</style>
"""
