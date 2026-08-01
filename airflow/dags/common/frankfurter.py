from datetime import datetime, timezone

import requests

URL = "https://api.frankfurter.dev/v2/rates"
ENTETES = {"User-Agent": "Mozilla/5.0"}


def recuperer(devises, debut=None, fin=None):
    params = {"base": "EUR", "quotes": ",".join(devises)}
    if debut:
        params["from"] = debut
    if fin:
        params["to"] = fin

    reponse = requests.get(URL, headers=ENTETES, params=params, timeout=30)
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


def garder_journees_completes(lignes, devises):
    """Les devises ne sortent pas toutes en meme temps : on ecarte les
    journees ou il en manque, sinon le trou reste definitif."""
    par_jour = {}
    for ligne in lignes:
        par_jour.setdefault(ligne["date_taux"], set()).add(ligne["devise_cible"])

    completes = {j for j, vues in par_jour.items() if set(devises) <= vues}
    ecartees = sorted(set(par_jour) - completes)
    return [l for l in lignes if l["date_taux"] in completes], ecartees
