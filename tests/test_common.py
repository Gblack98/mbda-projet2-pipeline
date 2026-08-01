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
