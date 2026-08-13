"""Session HTTP commune aux trois clients d'API.

Ces API publiques tombent et renvoient des 502. Le 2026-08-11, la Banque
Mondiale a mis plus de 60 s et toute l'execution a echoue. D'ou les reprises.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ENTETES = {"User-Agent": "Mozilla/5.0"}

# attentes de 2, 4 puis 8 secondes
TENTATIVES = 4
RECUL = 2


def session():
    s = requests.Session()
    s.headers.update(ENTETES)
    reprise = Retry(
        total=TENTATIVES - 1,
        connect=TENTATIVES - 1,
        read=TENTATIVES - 1,
        status=TENTATIVES - 1,
        backoff_factor=RECUL,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adaptateur = HTTPAdapter(max_retries=reprise)
    s.mount("https://", adaptateur)
    s.mount("http://", adaptateur)
    return s
