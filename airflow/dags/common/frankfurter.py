from datetime import datetime, timezone

import requests

URL = "https://api.frankfurter.dev/v2/rates"
ENTETES = {"User-Agent": "Mozilla/5.0"}


def recuperer(devises, debut):
    reponse = requests.get(URL, headers=ENTETES, timeout=60, params={
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
