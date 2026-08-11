from datetime import date, datetime, timezone

from . import reseau

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{}"


def _cotations_ticker(ticker, periode, recupere_le):
    reponse = reseau.session().get(
        URL.format(ticker), params={"range": periode, "interval": "1d"},
        timeout=30)
    reponse.raise_for_status()
    resultat = reponse.json()["chart"]["result"]
    if not resultat:
        return []

    bloc = resultat[0]
    valeurs = bloc["indicators"]["quote"][0]
    devise = bloc["meta"]["currency"]

    lignes = []
    for i, horodatage in enumerate(bloc["timestamp"]):
        cloture = valeurs["close"][i]
        if cloture is None:
            continue
        lignes.append({
            "date_cotation": date.fromtimestamp(horodatage).isoformat(),
            "instrument_id": ticker,
            "ouverture": valeurs["open"][i],
            "plus_haut": valeurs["high"][i],
            "plus_bas": valeurs["low"][i],
            "cloture": cloture,
            "volume": valeurs["volume"][i],
            "devise_cotation": devise,
            "recupere_le": recupere_le,
        })
    return lignes


def recuperer(tickers, periode="5d"):
    recupere_le = datetime.now(timezone.utc).isoformat()
    lignes = []
    for ticker in tickers:
        try:
            lignes += _cotations_ticker(ticker, periode, recupere_le)
        except Exception as err:
            print(f"{ticker} ignore : {err}")

    if not lignes:
        raise RuntimeError("aucune cotation recuperee")
    return lignes
