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

Airflow · BigQuery (Sandbox) · dbt Core · Power BI · Looker Studio

## Modèle

Granularité de la table de faits : **un instrument, un jour**.

```
dim_temps ┐
dim_instrument ├─► fct_cotation_journaliere
dim_devise ┤
dim_pays_exposition ┘
```

## Contraintes BigQuery Sandbox

- Pas de DML ni de streaming → chargement par lots
- Matérialisations dbt : `table` ou `view`, jamais `incremental`
- Tables expirées à 60 jours → tout doit être reconstructible

## Branches

`main` est protégée : fusion par pull request validée uniquement.

| Branche | |
|---|---|
| `gblack98` | ingestion, BigQuery |
| `nokho11` | dbt, tests |
| `isselmou` | restitution BI |

```bash
git checkout <ta-branche>
git pull
git commit -m "description courte"
git push
gh pr create --base main
```
