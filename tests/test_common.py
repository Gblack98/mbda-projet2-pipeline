import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import config, controles, schemas


def test_tickers_uniques():
    assert len(config.TICKERS) == len(set(config.TICKERS))


def test_hierarchie_complete():
    for ligne in config.INSTRUMENTS:
        assert all(ligne)


def test_devises_uniques():
    assert len(config.DEVISES) == len(set(config.DEVISES))
    assert "XOF" in config.DEVISES


def test_tables_sans_partition():
    for infos in schemas.TABLES.values():
        assert "partition" not in infos


def test_pays_uniques():
    assert len(config.PAYS) == len(set(config.PAYS))
    assert {"SEN", "MRT"} <= set(config.PAYS)


def test_indicateurs_export():
    assert len(config.INDICATEURS_EXPORT) == 4
    for categorie in config.INDICATEURS_EXPORT.values():
        assert categorie


def test_correspondance_secteurs_complete():
    secteurs = {i[3] for i in config.INSTRUMENTS}
    assert secteurs <= set(config.CATEGORIE_EXPORT)


def test_categories_export_connues():
    connues = set(config.INDICATEURS_EXPORT.values())
    for categorie in config.CATEGORIE_EXPORT.values():
        assert categorie is None or categorie in connues


def test_tables_vides_signale_les_zeros():
    volumes = {"cotations": 103127, "taux_change": 0, "devises": 16, "secteurs": 0}
    assert controles.tables_vides(volumes) == ["secteurs", "taux_change"]


def test_tables_vides_ne_signale_rien_quand_tout_est_charge():
    assert controles.tables_vides({"cotations": 1, "devises": 16}) == []


def test_instruments_manquants_repere_une_collecte_partielle():
    assert controles.instruments_manquants(["GC=F"], ["GC=F", "SI=F", "^VIX"]) \
        == ["SI=F", "^VIX"]


def test_instruments_manquants_vide_quand_la_collecte_est_complete():
    assert controles.instruments_manquants(config.TICKERS, config.TICKERS) == []


def test_barrick_cote_sous_son_symbole_actuel():
    # GOLD a ete repris par Gold.com, Inc. apres le changement de nom de
    # Barrick : correlation avec l'or de 0,215 au lieu de 0,655.
    assert "GOLD" not in config.TICKERS
    assert "B" in config.TICKERS
