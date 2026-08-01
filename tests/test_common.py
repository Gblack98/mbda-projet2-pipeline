import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import config, frankfurter


def test_tickers_uniques():
    assert len(config.TICKERS) == len(set(config.TICKERS))


def test_hierarchie_complete():
    for ligne in config.INSTRUMENTS:
        assert all(ligne)


def test_xof_suivi():
    assert "XOF" in config.DEVISES


def ligne(jour, devise):
    return {"date_taux": jour, "devise_cible": devise}


def test_journee_complete_gardee():
    devises = ["XOF", "NGN"]
    lignes = [ligne("2024-03-11", "XOF"), ligne("2024-03-11", "NGN")]
    gardees, ecartees = frankfurter.garder_journees_completes(lignes, devises)
    assert len(gardees) == 2 and ecartees == []


def test_journee_incomplete_ecartee():
    devises = ["XOF", "NGN"]
    gardees, ecartees = frankfurter.garder_journees_completes(
        [ligne("2024-03-12", "NGN")], devises)
    assert gardees == [] and ecartees == ["2024-03-12"]
