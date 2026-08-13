"""Session HTTP commune aux trois clients d'API.

Les trois sources sont des API publiques et gratuites : elles tombent, elles
ralentissent, elles renvoient des 502. Le DAG Airflow relance la tache trois
fois, mais scripts/ingest.py, que lance GitHub Actions, n'a aucune reprise et
c'est lui qui tourne en production.

Le 2026-08-11, l'API de la Banque Mondiale a depasse les 60 secondes et toute
l'execution a echoue, alors que les cotations etaient deja chargees. D'ou cette
session : quatre tentatives espacees par un recul exponentiel, sur les erreurs
reseau comme sur les codes 429 et 5xx.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ENTETES = {"User-Agent": "Mozilla/5.0"}

# 4 tentatives, attentes de 2, 4 puis 8 secondes.
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
