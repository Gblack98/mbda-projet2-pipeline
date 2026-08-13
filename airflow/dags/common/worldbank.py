from datetime import datetime, timezone

from . import reseau

URL = "https://api.worldbank.org/v2/country/{}/indicator/{}"


def recuperer(pays, indicateurs, depuis=2015):
    recupere_le = datetime.now(timezone.utc).isoformat()
    annee_max = datetime.now(timezone.utc).year
    lignes = []

    for code, categorie in indicateurs.items():
        # 120 s : cette API est la plus lente des trois et c'est elle qui a
        # fait tomber l'execution du 2026-08-11.
        reponse = reseau.session().get(
            URL.format(";".join(pays), code), timeout=120, params={
                "format": "json", "date": f"{depuis}:{annee_max}",
                "per_page": 1000})
        reponse.raise_for_status()
        corps = reponse.json()
        for r in corps[1] or []:
            if r["value"] is None:
                continue
            lignes.append({
                "pays": r["countryiso3code"],
                "annee": int(r["date"]),
                "categorie": categorie,
                "part_exportations": float(r["value"]),
                "recupere_le": recupere_le,
            })

    if not lignes:
        raise RuntimeError("aucune donnee d'exportations")
    return lignes
