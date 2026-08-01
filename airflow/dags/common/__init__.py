"""Briques partagées entre les DAGs et les scripts hors ordonnanceur.

Aucun module de ce paquet n'importe Airflow au niveau global : ils restent
utilisables et testables sans ordonnanceur.
"""
