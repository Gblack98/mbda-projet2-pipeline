"""Controles de qualite apres chargement.

Utilises par le DAG et par scripts/ingest.py, qui doivent refuser les memes
donnees. Rien d'Airflow ni de BigQuery ici, d'ou des tests sans reseau.
"""


def tables_vides(volumes):
    """volumes est un {nom de table: nombre de lignes}."""
    return sorted(table for table, lignes in volumes.items() if not lignes)


def instruments_manquants(instruments_charges, tickers_attendus):
    """Tickers demandes qui n'ont ramene aucune cotation.

    yahoo.recuperer ne leve que si les 41 echouent. Sans ce controle, une
    collecte reduite a un seul instrument passerait pour un succes.
    """
    return sorted(set(tickers_attendus) - set(instruments_charges))
