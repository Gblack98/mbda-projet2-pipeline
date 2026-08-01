# MBDA Projet 2 — Pipeline analytics

Pipeline quotidien sur 56 instruments financiers liés à l'économie ouest-africaine.
Master 1 MBDA — UN-CHK, 2026.

## Architecture

```
Yahoo Finance ┐
Frankfurter   ├─► Airflow ─► BigQuery.raw ─► dbt ─► BigQuery.marts ─► Power BI / Looker
Banque Mondiale ┘
```

## Sources

| Source | Données | Fréquence | Clé |
|---|---|---|---|
| Yahoo Finance | 41 instruments, OHLCV | quotidienne | non |
| Frankfurter (BCE) | 15 devises | quotidienne | non |
| Banque Mondiale | exportations par pays | annuelle | non |

## Modèle

Schéma en étoile. Granularité de la table de faits : **un instrument, un jour**.

```
dim_temps ┐
dim_instrument ├─► fct_cotation_journaliere
dim_devise ┤
dim_pays_exposition ┘
```

## Stack

Airflow · BigQuery (Sandbox) · dbt Core · Power BI · Looker Studio

## Contraintes BigQuery Sandbox

- Pas de DML, pas de streaming → chargement par lots
- Matérialisations dbt : `table` ou `view`, jamais `incremental`
- Expiration des tables à 60 jours → tout doit être reconstructible

## Branches

| Branche | Périmètre |
|---|---|
| `main` | protégée — merge par pull request validée uniquement |
| `feat/ingestion-airflow` | DAGs, appels API, chargement BigQuery |
| `feat/transformation-dbt` | modèles staging → marts, tests qualité |
| `feat/restitution-bi` | tableaux de bord, exports, captures |

Convention : `feat/`, `fix/`, `docs/` + description en kebab-case.

## Contribuer

```bash
git checkout feat/<branche>
git pull
# ... modifications ...
git commit -m "feat: description courte"
git push
gh pr create --base main
```

Une pull request nécessite **une validation** avant fusion.
