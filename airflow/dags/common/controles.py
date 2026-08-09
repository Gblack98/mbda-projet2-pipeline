"""Controles de qualite appliques apres chargement.

Partages par le DAG Airflow et par scripts/ingest.py : les deux chemins
alimentent les memes tables, ils doivent refuser les memes donnees. Les
fonctions ne touchent ni a Airflow ni a BigQuery, ce qui les rend testables
sans reseau.
"""


def tables_vides(volumes):
    """Tables chargees a zero ligne, dans l'ordre alphabetique.

    volumes est un dictionnaire {nom de table: nombre de lignes}.
    """
    return sorted(table for table, lignes in volumes.items() if not lignes)


def instruments_manquants(instruments_charges, tickers_attendus):
    """Tickers demandes qui n'ont ramene aucune cotation.

    yahoo.recuperer ignore les tickers en erreur et ne leve que si les 41
    echouent : sans ce controle, une collecte reduite a un seul instrument
    passerait pour un succes.
    """
    return sorted(set(tickers_attendus) - set(instruments_charges))
