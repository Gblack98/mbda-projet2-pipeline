"""Tests de la logique pure — aucun appel réseau, aucun accès BigQuery.

Ils tournent en une seconde et couvrent les décisions qui, si elles étaient
fausses, corrompraient l'entrepôt en silence : la détection des journées
partielles et la correspondance des sous-unités monétaires.

    python -m pytest tests/ -q
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "airflow", "dags"))

from common import config, frankfurter  # noqa: E402


# --- Cohérence de la configuration ---------------------------------------

def test_tickers_uniques():
    assert len(config.TICKERS) == len(set(config.TICKERS))


def test_hierarchie_complete():
    """Chaque instrument porte ses trois niveaux : sans quoi le cube a des trous."""
    for ticker, libelle, classe, secteur, sous_secteur in config.INSTRUMENTS:
        assert ticker and libelle and classe and secteur and sous_secteur


def test_devises_uniques():
    assert len(config.DEVISES) == len(set(config.DEVISES))


def test_xof_present_et_ancre():
    """Le XOF est la référence à volatilité nulle de toute l'analyse."""
    assert "XOF" in config.DEVISES
    assert config.REGIME_CHANGE["XOF"] == "Ancrage fixe"


# --- Sous-unités monétaires ----------------------------------------------

def test_sous_unites_divisees_par_cent():
    for devise in ("USX", "GBp", "ZAc"):
        diviseur, reelle = config.facteur_unite(devise)
        assert diviseur == 100.0
        assert reelle != devise


def test_devise_normale_inchangee():
    assert config.facteur_unite("USD") == (1.0, "USD")
    assert config.facteur_unite("EUR") == (1.0, "EUR")


def test_devise_inconnue_ne_casse_pas():
    """Une devise non répertoriée passe telle quelle plutôt que de lever."""
    assert config.facteur_unite("XYZ") == (1.0, "XYZ")


# --- Détection des journées partielles -----------------------------------

def _ligne(jour, devise):
    return {"date_taux": jour, "devise_cible": devise, "taux": 1.0}


def test_journee_complete_retenue():
    devises = ["XOF", "NGN", "GHS"]
    lignes = [_ligne("2026-07-31", d) for d in devises]
    completes, partielles = frankfurter.journees_completes(lignes, devises)
    assert completes == ["2026-07-31"]
    assert partielles == []


def test_journee_partielle_ecartee():
    """Le cas réel du 1er août : seul le naira était publié."""
    devises = ["XOF", "NGN", "GHS"]
    lignes = [_ligne("2026-08-01", "NGN")]
    completes, partielles = frankfurter.journees_completes(lignes, devises)
    assert completes == []
    assert partielles == ["2026-08-01"]


def test_melange_complet_et_partiel():
    devises = ["XOF", "NGN"]
    lignes = [
        _ligne("2026-07-31", "XOF"), _ligne("2026-07-31", "NGN"),
        _ligne("2026-08-01", "NGN"),
    ]
    completes, partielles = frankfurter.journees_completes(lignes, devises)
    assert completes == ["2026-07-31"]
    assert partielles == ["2026-08-01"]


def test_aucune_ligne():
    completes, partielles = frankfurter.journees_completes([], ["XOF"])
    assert completes == [] and partielles == []
