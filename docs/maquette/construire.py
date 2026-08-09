"""Construit la maquette autonome a partir du gabarit et des donnees reelles.

Lit les tables d'agregation de `marts`, les injecte dans gabarit.html a la place
de la ligne `const DONNEES = {};`, et ecrit tableau-de-bord.html. Le fichier
produit est autonome : ni serveur, ni reseau, ni bibliotheque externe.

    python docs/maquette/construire.py
"""

import json
import os
from datetime import date

from google.cloud import bigquery
from google.oauth2 import service_account

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.environ.get("MBDA_PROJECT", "crucial-bonsai-418120")
KEYFILE = os.path.expanduser(
    os.environ.get("MBDA_KEYFILE", "~/.gcp/mbda-projet2-sa.json"))
M = f"`{PROJET}`.marts"

# six paires representatives pour les nuages de points
PAIRES = ["barrick_or", "newmont_or", "kinross_or",
          "exxon_brent", "kosmos_gaz", "orange_or"]
# bornes du nuage : au-dela l'echelle ecrase tout le reste
BORNE = 12


def client():
    creds = service_account.Credentials.from_service_account_file(KEYFILE)
    return bigquery.Client(project=PROJET, credentials=creds)


def lire(bq, sql):
    lignes = []
    for r in bq.query(sql):
        d = {}
        for cle, v in r.items():
            if isinstance(v, date):
                d[cle] = v.isoformat()
            elif isinstance(v, float):
                d[cle] = round(v, 4)
            else:
                d[cle] = v
        lignes.append(d)
    return lignes


def collecter(bq):
    d = {}

    d["devises"] = lire(bq, f"""
        select devise_id, nom_devise, coefficient_variation, regime
        from {M}.dim_devise order by coefficient_variation, devise_id""")

    d["volatilite_classe"] = lire(bq, f"""
        select classe_actif, annee, instruments, observations,
               observations_ecartees, volatilite, volatilite_hors_anomalie,
               amplitude_moyenne
        from {M}.agg_volatilite_classe_annee order by classe_actif, annee""")

    d["tension"] = lire(bq, f"""
        select format_date('%Y-%m', mois) as mois, annee, volatilite,
               volatilite_hors_anomalie, mediane_historique, multiple_mediane,
               est_tension, observations, observations_ecartees
        from {M}.agg_tension_mensuelle order by mois""")

    d["correlations"] = lire(bq, f"""
        select paire_id, libelle, instrument_action, instrument_matiere, temoin,
               correlation, part_variance_expliquee, jours_communs
        from {M}.agg_correlation_instrument order by correlation desc""")

    d["exportations"] = lire(bq, f"""
        select pays, annee, categorie_export, part_exportations, rang_categorie,
               est_categorie_dominante, ecart_points
        from {M}.agg_exportations_evolution order by pays, annee, rang_categorie""")

    # volatilite d'ensemble par classe : ce n'est pas la moyenne des annees,
    # il faut la recalculer sur toutes les observations
    d["volatilite_totale"] = lire(bq, f"""
        select i.classe_actif,
               count(distinct f.instrument_id) as instruments,
               round(stddev(f.variation_pct), 4) as volatilite,
               round(stddev(if(f.variation_exploitable, f.variation_pct, null)), 4)
                   as volatilite_hors_anomalie
        from {M}.fct_cotation_journaliere f
        join {M}.dim_instrument i using (instrument_id)
        where f.variation_pct is not null
        group by i.classe_actif order by volatilite desc""")

    # quelques scalaires cites dans les tuiles
    d["faits"] = lire(bq, f"""
        select
          (select count(distinct taux) from `{PROJET}`.marts_staging.stg_taux_change
           where devise_cible = 'XOF') as valeurs_xof,
          (select count(*) from `{PROJET}`.marts_staging.stg_taux_change
           where devise_cible = 'XOF') as jours_xof,
          (select count(*) from {M}.fct_cotation_journaliere) as lignes_faits,
          (select countif(not variation_exploitable)
           from {M}.fct_cotation_journaliere) as lignes_ecartees""")[0]

    # nuages : dictionnaire paire -> liste de couples, format compact
    liste = ",".join(repr(p) for p in PAIRES)
    brut = lire(bq, f"""
        with v as (select date_cotation, instrument_id, variation_pct
                   from {M}.fct_cotation_journaliere where variation_exploitable)
        select p.paire_id, round(a.variation_pct, 2) as x,
               round(m.variation_pct, 2) as y
        from `{PROJET}`.marts_staging.paires_instrument p
        join v a on a.instrument_id = p.instrument_action
        join v m on m.instrument_id = p.instrument_matiere
                and m.date_cotation = a.date_cotation
        where p.paire_id in ({liste})
          and abs(a.variation_pct) <= {BORNE} and abs(m.variation_pct) <= {BORNE}""")
    nuages = {p: [] for p in PAIRES}
    for r in brut:
        nuages[r["paire_id"]].append([r["x"], r["y"]])
    d["nuages"] = nuages

    return d


def construire():
    bq = client()
    donnees = collecter(bq)

    gabarit = open(os.path.join(ICI, "gabarit.html"), encoding="utf-8").read()
    marque = "const DONNEES = {};"
    if marque not in gabarit:
        raise SystemExit("gabarit.html : ligne 'const DONNEES = {};' introuvable")

    charge = json.dumps(donnees, ensure_ascii=False, separators=(",", ":"))
    page = gabarit.replace(marque, f"const DONNEES = {charge};")

    sortie = os.path.join(ICI, "tableau-de-bord.html")
    open(sortie, "w", encoding="utf-8").write(page)

    for cle, v in donnees.items():
        if isinstance(v, dict) and cle == "faits":
            n = len(v)
        elif isinstance(v, dict):
            n = sum(len(x) for x in v.values())
        else:
            n = len(v)
        print(f"  {cle:20} {n:6} lignes")
    print(f"\n{sortie} — {os.path.getsize(sortie) / 1024:.0f} Ko")


if __name__ == "__main__":
    construire()
