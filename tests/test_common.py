import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airflow", "dags"))

from common import config, schemas


def test_tickers_uniques():
    assert len(config.TICKERS) == len(set(config.TICKERS))


def test_hierarchie_complete():
    for ligne in config.INSTRUMENTS:
        assert all(ligne)


def test_devises_uniques():
    assert len(config.DEVISES) == len(set(config.DEVISES))
    assert "XOF" in config.DEVISES


def test_tables_sans_partition():
    """Le Sandbox supprime les partitions de plus de 60 jours."""
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
    """Chaque secteur declare doit apparaitre dans la correspondance."""
    secteurs = {i[3] for i in config.INSTRUMENTS}
    assert secteurs <= set(config.CATEGORIE_EXPORT)


def test_categories_export_connues():
    """Les categories visees doivent exister cote Banque Mondiale."""
    connues = set(config.INDICATEURS_EXPORT.values())
    for categorie in config.CATEGORIE_EXPORT.values():
        assert categorie is None or categorie in connues
