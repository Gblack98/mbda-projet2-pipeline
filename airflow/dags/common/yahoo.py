"""Client Yahoo Finance — cours quotidiens OHLCV.

Interroge directement l'endpoint « chart » plutôt que de passer par yfinance :
une dépendance en moins, une réponse dont on maîtrise le format, et un
comportement identique en local comme dans Airflow.

La réponse expose deux tableaux parallèles — les horodatages d'un côté, les
valeurs de l'autre — qu'il faut recoudre par index. Les séances sans échange
apparaissent avec des valeurs nulles : elles sont écartées ici plutôt que
chargées, car une clôture nulle n'a pas de sens et ferait échouer le contrat
de schéma.
"""

from datetime import datetime, timezone, date
import time
import urllib.parse
import urllib.request
import json

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"
ENTETES = {"User-Agent": "Mozilla/5.0 (compatible; mbda-pipeline/1.0)"}
TIMEOUT = 30
TENTATIVES = 3
ATTENTE_INITIALE = 2  # secondes, doublée à chaque échec


class SourceIndisponible(RuntimeError):
    """La source n'a pas répondu après plusieurs tentatives."""


def _appel(ticker: str, params: dict) -> dict:
    """Appelle l'API avec relances exponentielles.

    Une erreur réseau ponctuelle ne doit pas faire échouer toute une
    exécution : on réessaie. En revanche, après épuisement des tentatives on
    lève une exception plutôt que de renvoyer une liste vide, sans quoi
    l'absence de données passerait pour une journée sans cotation.
    """
    url = URL.format(urllib.parse.quote(ticker)) + "?" + urllib.parse.urlencode(params)
    attente = ATTENTE_INITIALE
    derniere = None

    for essai in range(1, TENTATIVES + 1):
        try:
            requete = urllib.request.Request(url, headers=ENTETES)
            with urllib.request.urlopen(requete, timeout=TIMEOUT) as reponse:
                return json.loads(reponse.read())
        except Exception as err:  # réseau, HTTP, JSON illisible
            derniere = err
            if essai < TENTATIVES:
                time.sleep(attente)
                attente *= 2

    raise SourceIndisponible(f"{ticker} : {TENTATIVES} tentatives échouées ({derniere})")


def _lignes(charge_utile: dict, ticker: str, recupere_le: str) -> list:
    """Transforme la réponse brute en lignes prêtes pour BigQuery."""
    resultats = (charge_utile.get("chart") or {}).get("result")
    if not resultats:
        return []

    bloc = resultats[0]
    horodatages = bloc.get("timestamp") or []
    cotations = (bloc.get("indicators") or {}).get("quote") or [{}]
    cotations = cotations[0]
    devise = (bloc.get("meta") or {}).get("currency")

    if not horodatages or not devise:
        return []

    lignes = []
    for i, horodatage in enumerate(horodatages):
        cloture = _valeur(cotations, "close", i)
        if cloture is None:
            continue  # séance sans échange : rien à charger

        lignes.append({
            "date_cotation": date.fromtimestamp(horodatage).isoformat(),
            "instrument_id": ticker,
            "ouverture": _valeur(cotations, "open", i),
            "plus_haut": _valeur(cotations, "high", i),
            "plus_bas": _valeur(cotations, "low", i),
            "cloture": cloture,
            "volume": _entier(cotations, "volume", i),
            "devise_cotation": devise,
            "recupere_le": recupere_le,
        })

    return lignes


def _valeur(cotations: dict, champ: str, i: int):
    serie = cotations.get(champ) or []
    return serie[i] if i < len(serie) else None


def _entier(cotations: dict, champ: str, i: int):
    brut = _valeur(cotations, champ, i)
    return int(brut) if brut is not None else None


def recuperer(tickers, periode="5d", intervalle="1d") -> list:
    """Récupère les cotations d'une liste de tickers.

    `periode` accepte les valeurs de l'API : 5d, 1mo, 2y, 10y…
    Attention, `max` fait basculer la réponse en granularité mensuelle ;
    pour dix ans de données quotidiennes il faut demander « 10y ».
    """
    recupere_le = datetime.now(timezone.utc).isoformat()
    lignes = []
    echecs = []

    for ticker in tickers:
        try:
            charge = _appel(ticker, {"range": periode, "interval": intervalle})
            lignes.extend(_lignes(charge, ticker, recupere_le))
        except SourceIndisponible as err:
            echecs.append(str(err))

    if echecs:
        # Un instrument retiré de la cote ne doit pas bloquer les quarante
        # autres, mais l'incident doit rester visible dans les journaux.
        print(f"[yahoo] {len(echecs)} instrument(s) en échec :")
        for echec in echecs:
            print(f"  - {echec}")

    if not lignes:
        raise SourceIndisponible("aucune cotation récupérée pour aucun instrument")

    return lignes
