"""Client Frankfurter — taux de change publiés par la Banque Centrale Européenne.

L'endpoint `/v2/rates` attend le paramètre `quotes` (et non `symbols`, qui
renvoie une erreur 422) et répond par une liste plate, un enregistrement par
couple date/devise :

    [{"date": "2026-07-31", "base": "EUR", "quote": "NGN", "rate": 1565.99}, …]

Les devises ne sont pas publiées toutes en même temps : il arrive qu'une
journée ne contienne que le naira, les autres arrivant plus tard. Le
chargement doit donc tolérer une couverture partielle, et le contrôle de
complétude est fait à part, par `journees_completes`.
"""

from datetime import datetime, timezone
import time
import urllib.parse
import urllib.request
import json

URL = "https://api.frankfurter.dev/v2/rates"
URL_DEVISES = "https://api.frankfurter.dev/v2/currencies"
# Sans en-tête explicite, urllib s'annonce « Python-urllib » et la source
# répond 403.
ENTETES = {"User-Agent": "mbda-pipeline/1.0"}
TIMEOUT = 30
TENTATIVES = 3
ATTENTE_INITIALE = 2


class SourceIndisponible(RuntimeError):
    """La source n'a pas répondu après plusieurs tentatives."""


def _appel(url: str, params: dict = None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    attente = ATTENTE_INITIALE
    derniere = None

    for essai in range(1, TENTATIVES + 1):
        try:
            requete = urllib.request.Request(url, headers=ENTETES)
            with urllib.request.urlopen(requete, timeout=TIMEOUT) as reponse:
                return json.loads(reponse.read())
        except Exception as err:
            derniere = err
            if essai < TENTATIVES:
                time.sleep(attente)
                attente *= 2

    raise SourceIndisponible(f"{url} : {TENTATIVES} tentatives échouées ({derniere})")


def recuperer(devises, debut=None, fin=None, date_precise=None) -> list:
    """Récupère les taux EUR -> devises cibles.

    Sans argument de date, renvoie les taux les plus récents. `debut`/`fin`
    délimitent une plage au format YYYY-MM-DD.
    """
    params = {"base": "EUR", "quotes": ",".join(devises)}
    if date_precise:
        params["date"] = date_precise
    if debut:
        params["from"] = debut
    if fin:
        params["to"] = fin

    charge = _appel(URL, params)
    recupere_le = datetime.now(timezone.utc).isoformat()

    lignes = [
        {
            "date_taux": enreg["date"],
            "devise_base": enreg["base"],
            "devise_cible": enreg["quote"],
            "taux": float(enreg["rate"]),
            "recupere_le": recupere_le,
        }
        for enreg in charge
        if enreg.get("rate") is not None
    ]

    if not lignes:
        raise SourceIndisponible("aucun taux renvoyé par la source")

    return lignes


def recuperer_dimension_devises() -> list:
    """Métadonnées des devises : nom, symbole, code ISO, dates de validité.

    La source fournit une dimension prête à l'emploi, ce qui évite de saisir
    à la main les libellés de quatorze monnaies.
    """
    charge = _appel(URL_DEVISES)
    return [
        {
            "devise_id": d["iso_code"],
            "libelle": d.get("name"),
            "symbole": d.get("symbol"),
            "code_numerique": d.get("iso_numeric"),
            "publie_depuis": d.get("start_date"),
            "publie_jusqua": d.get("end_date"),
        }
        for d in charge
    ]


def journees_completes(lignes, devises) -> tuple:
    """Sépare les journées entièrement publiées de celles qui sont partielles.

    Renvoie (journées complètes, journées partielles). Charger une journée
    partielle produirait des trous qu'aucune exécution ultérieure ne
    viendrait combler, puisque le DAG ne repasse pas sur le passé.
    """
    attendu = set(devises)
    par_jour = {}
    for ligne in lignes:
        par_jour.setdefault(ligne["date_taux"], set()).add(ligne["devise_cible"])

    completes = sorted(j for j, vues in par_jour.items() if attendu <= vues)
    partielles = sorted(j for j, vues in par_jour.items() if not attendu <= vues)
    return completes, partielles
