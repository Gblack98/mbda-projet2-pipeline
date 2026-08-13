from datetime import datetime, timezone

from . import reseau

URL = "https://api.frankfurter.dev/v2/rates"


def recuperer(devises, debut):
    reponse = reseau.session().get(URL, timeout=60, params={
        "base": "EUR", "quotes": ",".join(devises), "from": debut})
    reponse.raise_for_status()
    recupere_le = datetime.now(timezone.utc).isoformat()

    lignes = [{
        "date_taux": t["date"],
        "devise_base": t["base"],
        "devise_cible": t["quote"],
        "taux": float(t["rate"]),
        "recupere_le": recupere_le,
    } for t in reponse.json() if t.get("rate") is not None]

    if not lignes:
        raise RuntimeError("aucun taux recupere")
    return lignes


URL_DEVISES = "https://api.frankfurter.dev/v2/currencies"


def devises(codes):
    reponse = reseau.session().get(URL_DEVISES, timeout=30)
    reponse.raise_for_status()
    return [{
        "devise_id": c["iso_code"],
        "libelle": c["name"],
        "symbole": c["symbol"],
        "publiee_depuis": c["start_date"],
        "publiee_jusqua": c["end_date"],
    } for c in reponse.json() if c["iso_code"] in codes]
