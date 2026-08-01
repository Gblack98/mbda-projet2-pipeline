"""Configuration centrale du pipeline.

Un seul endroit décrit l'univers suivi et la cible BigQuery. Les DAGs, les
scripts hors ordonnanceur et les tests lisent tous d'ici : deux définitions
divergentes provoqueraient des chargements incohérents.
"""

import os

# --- Cible BigQuery -------------------------------------------------------

PROJET = os.environ.get("MBDA_PROJECT", "crucial-bonsai-418120")
DATASET_RAW = os.environ.get("MBDA_DATASET_RAW", "raw")
DATASET_MARTS = os.environ.get("MBDA_DATASET_MARTS", "marts")
KEYFILE = os.path.expanduser(
    os.environ.get("MBDA_KEYFILE", "~/.gcp/mbda-projet2-sa.json")
)
LOCATION = "EU"

TABLE_COTATIONS = "cotations"
TABLE_TAUX = "taux_change"

# --- Univers suivi --------------------------------------------------------
# (ticker, libellé, classe d'actif, secteur, sous-secteur)
#
# Les tickers sont ceux de Yahoo Finance. La hiérarchie à trois niveaux est
# reprise telle quelle dans dim_instrument : c'est elle qui rend le cube
# navigable (dérouler « matières premières » vers « agricoles » vers « cacao »).

INSTRUMENTS = [
    # -- Matières premières : agricoles
    ("CC=F", "Cacao", "Matières premières", "Agricoles", "Cultures tropicales"),
    ("KC=F", "Café", "Matières premières", "Agricoles", "Cultures tropicales"),
    ("SB=F", "Sucre", "Matières premières", "Agricoles", "Cultures tropicales"),
    ("CT=F", "Coton", "Matières premières", "Agricoles", "Fibres"),
    ("OJ=F", "Jus d'orange", "Matières premières", "Agricoles", "Cultures tropicales"),
    # -- Matières premières : céréales
    ("ZW=F", "Blé", "Matières premières", "Céréales", "Céréales panifiables"),
    ("ZC=F", "Maïs", "Matières premières", "Céréales", "Céréales fourragères"),
    ("ZS=F", "Soja", "Matières premières", "Céréales", "Oléagineux"),
    ("ZR=F", "Riz", "Matières premières", "Céréales", "Céréales panifiables"),
    ("ZO=F", "Avoine", "Matières premières", "Céréales", "Céréales fourragères"),
    # -- Matières premières : énergie
    ("BZ=F", "Pétrole Brent", "Matières premières", "Énergie", "Pétrole"),
    ("CL=F", "Pétrole WTI", "Matières premières", "Énergie", "Pétrole"),
    ("NG=F", "Gaz naturel", "Matières premières", "Énergie", "Gaz"),
    ("RB=F", "Essence", "Matières premières", "Énergie", "Produits raffinés"),
    ("HO=F", "Fioul domestique", "Matières premières", "Énergie", "Produits raffinés"),
    # -- Matières premières : métaux
    ("GC=F", "Or", "Matières premières", "Métaux précieux", "Or"),
    ("SI=F", "Argent", "Matières premières", "Métaux précieux", "Argent"),
    ("PL=F", "Platine", "Matières premières", "Métaux précieux", "Platinoïdes"),
    ("PA=F", "Palladium", "Matières premières", "Métaux précieux", "Platinoïdes"),
    ("HG=F", "Cuivre", "Matières premières", "Métaux industriels", "Cuivre"),
    ("TIO=F", "Minerai de fer", "Matières premières", "Métaux industriels", "Fer"),
    ("ALI=F", "Aluminium", "Matières premières", "Métaux industriels", "Aluminium"),
    # -- Matières premières : élevage
    ("LE=F", "Bovins", "Matières premières", "Élevage", "Bovins"),
    # -- Actions : hydrocarbures
    ("KOS", "Kosmos Energy", "Actions", "Hydrocarbures", "Exploration-production"),
    ("BP", "BP", "Actions", "Hydrocarbures", "Intégré"),
    ("WDS", "Woodside Energy", "Actions", "Hydrocarbures", "Exploration-production"),
    ("TTE.PA", "TotalEnergies", "Actions", "Hydrocarbures", "Intégré"),
    ("SHEL.L", "Shell", "Actions", "Hydrocarbures", "Intégré"),
    ("XOM", "Exxon Mobil", "Actions", "Hydrocarbures", "Intégré"),
    # -- Actions : mines
    ("KGC", "Kinross Gold", "Actions", "Mines", "Or"),
    ("EDV.TO", "Endeavour Mining", "Actions", "Mines", "Or"),
    ("GOLD", "Barrick", "Actions", "Mines", "Or"),
    ("NEM", "Newmont", "Actions", "Mines", "Or"),
    ("GLEN.L", "Glencore", "Actions", "Mines", "Diversifié"),
    ("AGL.JO", "Anglo American", "Actions", "Mines", "Diversifié"),
    # -- Actions : télécoms
    ("ORA.PA", "Orange", "Actions", "Télécoms", "Opérateur"),
    # -- Indices
    ("^GSPC", "S&P 500", "Indices", "Actions", "États-Unis"),
    ("^FCHI", "CAC 40", "Indices", "Actions", "France"),
    ("^FTSE", "FTSE 100", "Indices", "Actions", "Royaume-Uni"),
    ("^N225", "Nikkei 225", "Indices", "Actions", "Japon"),
    ("^VIX", "VIX", "Indices", "Volatilité", "États-Unis"),
]

TICKERS = [i[0] for i in INSTRUMENTS]

# --- Devises --------------------------------------------------------------
# Cotées contre l'euro par la Banque Centrale Européenne.
# Le XOF est arrimé à l'euro à taux fixe : sa volatilité nulle sert de
# référence pour comparer les régimes de change.

DEVISES = [
    "XOF", "MRU", "NGN", "GHS", "GMD", "CVE",
    "USD", "GBP", "JPY", "CNY", "ZAR", "MAD", "EGP", "KES",
]

REGIME_CHANGE = {"XOF": "Ancrage fixe"}
REGIME_DEFAUT = "Flottant"

# --- Sous-unités monétaires ----------------------------------------------
# Yahoo Finance cote certains instruments en centimes. Sans correction, le
# coton (81 USX) paraîtrait cent fois moins cher qu'il ne l'est.
# Le facteur est stocké en base plutôt qu'appliqué à l'ingestion : les
# données brutes restent fidèles à la source, la correction relève de dbt.

FACTEURS_UNITE = {
    "USX": (100.0, "USD"),   # cents américains
    "GBp": (100.0, "GBP"),   # pence britanniques
    "ZAc": (100.0, "ZAR"),   # cents sud-africains
    "ILA": (100.0, "ILS"),   # agorot israéliens
}


def facteur_unite(devise_cotation: str):
    """Renvoie (diviseur, devise réelle) pour une devise de cotation."""
    return FACTEURS_UNITE.get(devise_cotation, (1.0, devise_cotation))
