# Architecture

![Pipeline](img/pipeline.gif)

(version statique : `img/architecture.png`)

## Sources

| Source | Contenu | Fréquence |
|---|---|---|
| Yahoo Finance | 41 instruments, OHLCV | quotidienne |
| Frankfurter (BCE) | 15 devises | quotidienne |
| Banque Mondiale | exportations par pays | annuelle |

Aucune ne demande de clé.

## Ingestion

Le DAG `ingest_market_data` tourne les jours ouvrés à 18h et remplit `raw` :

| Table | Lignes |
|---|---|
| `cotations` | ~103 000 |
| `taux_change` | ~47 000 |
| `instruments` | 41 |
| `devises` | 16 |
| `exportations` | 300 |
| `secteurs` | 11 |

Chaque exécution réécrit les tables entières (`WRITE_TRUNCATE`). Dix ans font
34 Mo, l'incrémental n'apporterait rien et le rejeu reste sans effet de bord.

`scripts/ingest.py` fait la même chose sans ordonnanceur.

## Modèle

![Modèle](img/schema_etoile.png)

Grain de la table de faits : un instrument, un jour.

## À savoir

- Yahoo cote certains instruments en centimes (`USX`, `GBp`, `ZAc`) — `raw`
  garde la valeur brute, la division se fait dans dbt.
- Les devises ne sont pas toutes publiées le même jour, d'où des journées
  partielles dans `taux_change`.
- Le MRU n'existe que depuis janvier 2018.
- Le Sandbox interdit le DML et purge les partitions au-delà de 60 jours :
  chargement par lots, pas de partitionnement par date.

## Exécution automatique

`.github/workflows/pipeline.yml` lance l'ingestion puis `dbt build` les jours
ouvrés à 18h, et envoie un mail si une étape échoue.

Secrets à définir dans les paramètres du dépôt :

| Secret | Contenu |
|---|---|
| `GCP_SA_KEY` | clé de service BigQuery (JSON) |
| `MAIL_USER` | adresse Gmail d'envoi |
| `MAIL_PASSWORD` | mot de passe d'application Gmail |
| `MAIL_TO` | destinataires, séparés par des virgules |

Le mot de passe d'application se crée sur myaccount.google.com/apppasswords
et suppose la validation en deux étapes activée. Le mot de passe habituel ne
fonctionne pas.

## Régénérer les schémas

```bash
python docs/schemas.py
```
