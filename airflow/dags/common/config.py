import os

PROJET = os.environ.get("MBDA_PROJECT", "crucial-bonsai-418120")
DATASET = os.environ.get("MBDA_DATASET", "raw")
KEYFILE = os.path.expanduser(os.environ.get("MBDA_KEYFILE", "~/.gcp/mbda-projet2-sa.json"))
LOCATION = "EU"

# ticker, libelle, classe, secteur, sous-secteur
INSTRUMENTS = [
    ("CC=F", "Cacao", "Matieres premieres", "Agricoles", "Cultures tropicales"),
    ("KC=F", "Cafe", "Matieres premieres", "Agricoles", "Cultures tropicales"),
    ("SB=F", "Sucre", "Matieres premieres", "Agricoles", "Cultures tropicales"),
    ("CT=F", "Coton", "Matieres premieres", "Agricoles", "Fibres"),
    ("OJ=F", "Jus d'orange", "Matieres premieres", "Agricoles", "Cultures tropicales"),
    ("ZW=F", "Ble", "Matieres premieres", "Cereales", "Panifiables"),
    ("ZC=F", "Mais", "Matieres premieres", "Cereales", "Fourrageres"),
    ("ZS=F", "Soja", "Matieres premieres", "Cereales", "Oleagineux"),
    ("ZR=F", "Riz", "Matieres premieres", "Cereales", "Panifiables"),
    ("ZO=F", "Avoine", "Matieres premieres", "Cereales", "Fourrageres"),
    ("BZ=F", "Petrole Brent", "Matieres premieres", "Energie", "Petrole"),
    ("CL=F", "Petrole WTI", "Matieres premieres", "Energie", "Petrole"),
    ("NG=F", "Gaz naturel", "Matieres premieres", "Energie", "Gaz"),
    ("RB=F", "Essence", "Matieres premieres", "Energie", "Raffines"),
    ("HO=F", "Fioul", "Matieres premieres", "Energie", "Raffines"),
    ("GC=F", "Or", "Matieres premieres", "Metaux precieux", "Or"),
    ("SI=F", "Argent", "Matieres premieres", "Metaux precieux", "Argent"),
    ("PL=F", "Platine", "Matieres premieres", "Metaux precieux", "Platinoides"),
    ("PA=F", "Palladium", "Matieres premieres", "Metaux precieux", "Platinoides"),
    ("HG=F", "Cuivre", "Matieres premieres", "Metaux industriels", "Cuivre"),
    ("TIO=F", "Minerai de fer", "Matieres premieres", "Metaux industriels", "Fer"),
    ("ALI=F", "Aluminium", "Matieres premieres", "Metaux industriels", "Aluminium"),
    ("LE=F", "Bovins", "Matieres premieres", "Elevage", "Bovins"),
    ("KOS", "Kosmos Energy", "Actions", "Hydrocarbures", "Exploration"),
    ("BP", "BP", "Actions", "Hydrocarbures", "Integre"),
    ("WDS", "Woodside", "Actions", "Hydrocarbures", "Exploration"),
    ("TTE.PA", "TotalEnergies", "Actions", "Hydrocarbures", "Integre"),
    ("SHEL.L", "Shell", "Actions", "Hydrocarbures", "Integre"),
    ("XOM", "Exxon Mobil", "Actions", "Hydrocarbures", "Integre"),
    ("KGC", "Kinross Gold", "Actions", "Mines", "Or"),
    ("EDV.TO", "Endeavour Mining", "Actions", "Mines", "Or"),
    ("GOLD", "Barrick", "Actions", "Mines", "Or"),
    ("NEM", "Newmont", "Actions", "Mines", "Or"),
    ("GLEN.L", "Glencore", "Actions", "Mines", "Diversifie"),
    ("AGL.JO", "Anglo American", "Actions", "Mines", "Diversifie"),
    ("ORA.PA", "Orange", "Actions", "Telecoms", "Operateur"),
    ("^GSPC", "S&P 500", "Indices", "Actions", "Etats-Unis"),
    ("^FCHI", "CAC 40", "Indices", "Actions", "France"),
    ("^FTSE", "FTSE 100", "Indices", "Actions", "Royaume-Uni"),
    ("^N225", "Nikkei 225", "Indices", "Actions", "Japon"),
    ("^VIX", "VIX", "Indices", "Volatilite", "Etats-Unis"),
]

TICKERS = [i[0] for i in INSTRUMENTS]

DEVISES = ["XOF", "MRU", "NGN", "GHS", "GMD", "CVE",
           "USD", "GBP", "JPY", "CNY", "ZAR", "MAD", "EGP", "KES", "CAD"]

# L'euro sert de base aux taux : il n'a pas de cours, mais doit figurer dans
# la dimension pour que les cotations en euros aient une devise rattachee.
DEVISES_DIMENSION = DEVISES + ["EUR"]

# Yahoo cote certains instruments en centimes.
SOUS_UNITES = {"USX": "USD", "GBp": "GBP", "ZAc": "ZAR"}

# Profondeur d'historique rechargee a chaque execution.
PROFONDEUR = "10y"
PROFONDEUR_JOURS = 3650

# Pays suivis (codes ISO3) et indicateurs Banque Mondiale : part de chaque
# categorie dans les exportations de marchandises.
PAYS = ["SEN", "MRT", "NGA", "GHA", "CIV", "MLI", "BFA", "BEN"]

INDICATEURS_EXPORT = {
    "TX.VAL.FUEL.ZS.UN": "Energie",
    "TX.VAL.MMTL.ZS.UN": "Metaux",
    "TX.VAL.AGRI.ZS.UN": "Agricoles",
    "TX.VAL.FOOD.ZS.UN": "Alimentaire",
}

# Rattachement des secteurs aux categories d'exportation de la Banque Mondiale.
# Declare explicitement car la relation est N:1 : joindre sur le libelle
# produirait des doublons et laisserait des categories sans correspondance.
CATEGORIE_EXPORT = {
    "Energie": "Energie",
    "Hydrocarbures": "Energie",
    "Metaux precieux": "Metaux",
    "Metaux industriels": "Metaux",
    "Mines": "Metaux",
    "Agricoles": "Agricoles",
    "Cereales": "Alimentaire",
    "Elevage": "Alimentaire",
    "Telecoms": None,
    "Actions": None,
    "Volatilite": None,
}
