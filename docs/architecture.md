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

Le DAG `ingest_market_data` tourne les jours ouvrés à 18h.

```
preparer
   ├── cotations ──────┐
   ├── taux ───────────┤
   ├── instruments ────┤
   ├── devises ────────┼── controler_qualite ── dbt_deps ── dbt_run ── dbt_test
   ├── secteurs ───────┤
   └── exportations ───┘

controler_qualite ── dbt_deps ── dbt_seed ── dbt_run ── dbt_test ── dbt_docs
```

`dbt_seed` charge la table de correspondance des devises, dont dépend
`fct_cotation_journaliere`. `dbt_docs` produit la documentation navigable dans
`dbt_pipeline/target/index.html`.

Chaque source est chargée par sa propre tâche : une panne côté Banque Mondiale
n'empêche pas les autres d'aboutir, et Airflow ne relance que celle qui a
échoué. `controler_qualite` interrompt le DAG si une table est vide ou si le
nombre d'instruments ne correspond pas à la configuration.

L'échec de n'importe quelle tâche déclenche un mail. Les identifiants viennent
de `MBDA_SMTP_USER`, `MBDA_SMTP_PASSWORD` et `MBDA_SMTP_TO` ; sans eux
l'alerte est ignorée sans faire échouer la tâche.

Contenu de `raw` :

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

## Deux ordonnanceurs, un seul à activer

Le DAG Airflow et le workflow GitHub Actions couvrent le même périmètre, à la
même heure. N'en activer qu'un : Airflow pour une démonstration ou une
machine allumée en continu, Actions pour une exécution autonome.

## Exécution automatique

Deux déclencheurs couvrent le même calendrier (jours ouvrés, 18h) — n'en
activer qu'un seul en production, sinon deux `WRITE_TRUNCATE` concurrents
peuvent écraser les mêmes tables au même moment :

- **`.github/workflows/pipeline.yml`** (par défaut) — enchaîne l'ingestion
  puis `dbt build`, envoie un mail si une étape échoue. Ne nécessite aucun
  orchestrateur déployé.
- **Le DAG `ingest_market_data`** (Airflow) — pipeline complet autonome :
  ingestion puis `dbt deps && dbt build` (tâche `transformer`). À réserver à
  qui dispose déjà d'un Airflow déployé ; le worker doit avoir
  `pip install -r requirements.txt` (dbt inclus) et un accès à
  `MBDA_KEYFILE`/aux identifiants BigQuery.

Secrets à définir dans les paramètres du dépôt (pour le déclencheur GitHub
Actions) :

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

Les diagrammes sont des pages HTML capturées avec Chrome en mode headless.

```bash
python docs/diagramme/frames.py   # architecture animée + version statique
python docs/diagramme/rendre.py   # modèle dimensionnel
```

`docs/diagramme/architecture.drawio` est une version éditable du même schéma :
elle s'ouvre sur app.diagrams.net et s'exporte en GIF animé depuis
`Fichier > Exporter > GIF animé`. Régénérée par `python docs/diagramme/drawio.py`.
