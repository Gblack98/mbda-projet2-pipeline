# Pipeline analytics — matières premières et devises

Collecte quotidienne de 56 instruments financiers, structurés en schéma en étoile.

```
Yahoo Finance ┐
Frankfurter   ├─► Airflow ─► BigQuery.raw ─► dbt ─► BigQuery.marts ─► BI
Banque Mondiale ┘
```

## Sources

| Source | Données | Fréquence | Clé |
|---|---|---|---|
| Yahoo Finance | 41 instruments, OHLCV | quotidienne | non |
| Frankfurter (BCE) | 15 devises | quotidienne | non |
| Banque Mondiale | exportations par pays | annuelle | non |

## Stack

Airflow · BigQuery · dbt Core · Power BI · Looker Studio

## Modèle

Granularité de la table de faits : **un instrument, un jour**.

```
dim_temps ┐
dim_instrument ├─► fct_cotation_journaliere
dim_devise ┤
dim_pays_exposition ┘
```
