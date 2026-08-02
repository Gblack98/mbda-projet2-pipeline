# Architecture

## Vue d'ensemble

![Pipeline](img/pipeline.gif)

![Architecture](img/architecture.png)

Trois sources publiques alimentent un DAG Airflow quotidien, qui charge les
données brutes dans BigQuery. dbt les transforme en schéma en étoile, exploité
par les outils de restitution.

Deux règles structurent l'ensemble :

- `raw` n'est jamais modifié — c'est une copie fidèle des sources
- chaque exécution recharge tout (`WRITE_TRUNCATE`), ce qui rend le pipeline
  idempotent : le rejouer aboutit au même état

## Sources

| Source | Contenu | Fréquence | Clé |
|---|---|---|---|
| Yahoo Finance | 41 instruments, OHLCV | quotidienne | non |
| Frankfurter (BCE) | 14 devises, taux EUR | quotidienne | non |
| Banque Mondiale | 8 pays, parts d'exportations | annuelle | non |

## Le DAG

`ingest_market_data`, du lundi au vendredi à 18h00 (après clôture des marchés).

```
preparer ─┬─ cotations  ─┐
          ├─ taux       ─┼─ controler
          └─ references ─┘
```

Les trois collectes sont indépendantes : l'échec de l'une n'empêche pas les
autres d'aboutir.

Une exécution complète dure environ 90 secondes pour 34 Mo, soit 0,003 % du
quota mensuel de 1 To. À ce volume, un chargement incrémental serait plus
complexe sans être plus rapide.

## Base de données

### `raw` — état actuel

| Table | Lignes | Source |
|---|---|---|
| `cotations` | 103 104 | Yahoo Finance |
| `taux_change` | 43 382 | Frankfurter |
| `instruments` | 41 | configuration du projet |
| `devises` | 14 | Frankfurter `/v2/currencies` |
| `exportations` | 300 | Banque Mondiale `TX.VAL.*` |

```
cotations                        taux_change
├─ date_cotation    DATE         ├─ date_taux      DATE
├─ instrument_id    STRING ─┐    ├─ devise_base    STRING
├─ ouverture        FLOAT   │    ├─ devise_cible   STRING ─┐
├─ plus_haut        FLOAT   │    ├─ taux           FLOAT   │
├─ plus_bas         FLOAT   │    └─ recupere_le    TS      │
├─ cloture          FLOAT   │                              │
├─ volume           INTEGER │    devises                   │
├─ devise_cotation  STRING  │    ├─ devise_id      STRING ◀┘
└─ recupere_le      TS      │    ├─ libelle        STRING
                            │    ├─ symbole        STRING
instruments                 │    ├─ publiee_depuis DATE
├─ instrument_id    STRING ◀┘    └─ publiee_jusqua DATE
├─ libelle          STRING
├─ classe_actif     STRING       exportations
├─ secteur          STRING       ├─ pays               STRING
└─ sous_secteur     STRING       ├─ annee              INTEGER
                                 ├─ categorie          STRING
                                 └─ part_exportations  FLOAT
```

### `marts` — schéma en étoile à construire

![Schéma en étoile](img/schema_etoile.png)

Granularité de la table de faits : **un instrument, un jour**.

| Table cible | Construite depuis |
|---|---|
| `fct_cotation_journaliere` | `cotations` + `taux_change` |
| `dim_temps` | dérivée des dates |
| `dim_instrument` | `instruments` |
| `dim_devise` | `devises` + `taux_change` |
| contexte pays | `exportations` |

## Points d'attention pour la transformation

**Unités de cotation.** Yahoo cote 12 instruments en centimes : `USX` (cents
américains), `GBp` (pence), `ZAc` (cents sud-africains). Sans division par 100,
Anglo American à 83 823 passe pour l'action la plus chère de la table. La
devise brute est conservée dans `cotations.devise_cotation`.

**Journées de taux incomplètes.** Les devises ne sont pas publiées
simultanément — certaines journées n'en contiennent qu'une partie. `raw` les
conserve telles quelles ; le filtrage relève du staging.

**MRU avant 2018.** Le nouvel ouguiya n'existe que depuis le 2 janvier 2018.
Son absence sur les années antérieures est normale, ce n'est pas un trou de
données.

**Régime de change.** Volontairement non déclaré en base : il se dérive de la
variance des taux (une devise dont le taux ne varie jamais est arrimée). Éviter
une saisie manuelle, plusieurs devises ayant des régimes non évidents.

## Contraintes BigQuery Sandbox

Le mode gratuit interdit les instructions DML et l'insertion en flux continu :
le chargement se fait donc par lots.

Les tables expirent après 60 jours. Le DAG les recrée au passage suivant, ce
qui rend le pipeline auto-réparant tant qu'il tourne.

Toute partition de plus de 60 jours est supprimée automatiquement, et ce
comportement ne peut pas être désactivé — d'où l'absence de partitionnement par
date métier, qui réduirait l'historique aux deux derniers mois. Les tables sont
clusterisées à la place.

## Régénérer les schémas

```bash
python docs/schemas.py
```
