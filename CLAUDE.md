# Repères du dépôt

Notes durables sur ce projet : ce qui a été décidé, ce qui a déjà été essayé, et
les pièges qui ont coûté du temps. À lire avant de proposer un changement.

## Le projet

Devoir du module Bases de Données Multidimensionnelles, Master 1 MBDA, UN-CHK.
Trinôme : Ibrahima Gabar Diop (`Gblack98`), Ndeye Sokhna (`Nokho11`), Isselmou
(`isselmou85`).

Pipeline quotidien sur 41 instruments financiers et 15 devises, schéma en
étoile dans BigQuery, restitution par une application Streamlit. Cinq questions
métier, détaillées dans `docs/questions-metier.md`.

Isselmou n'utilise pas GitHub : il fait le tableau de bord et a déjà l'accès
BigQuery. `docs/questions-metier.md` est écrit pour lui.

## Environnements

**Airflow et dbt ne cohabitent pas.** Leurs versions de `google-cloud-*` sont
incompatibles. Deux environnements séparés, deux fichiers de dépendances :

- `requirements.txt` : ingestion, dbt, tests. C'est ce qu'installe GitHub Actions.
- `requirements-airflow.txt` : l'ordonnanceur seul, Airflow 2.9.3 sous Python
  3.12, à installer avec son fichier de contraintes.

Conséquence : le DAG appelle dbt par le **chemin explicite** de son venv, jamais
par le `PATH`, et jamais par `subprocess.run(["dbt"])`.

`airflow standalone` relance ses sous-processus via le `PATH` : pointer le
binaire ne suffit pas, il faut `export PATH="$VENV/bin:$PATH"`. C'est ce que
fait `demarrer.sh`.

**Airflow 2.x et 3.x ne sont pas interchangeables.** L'équipe tourne sur les
deux. Deux écarts déjà rencontrés :

- `BashOperator` a quitté le coeur pour le provider `standard` en 3.0. L'import
  du DAG essaie les deux chemins.
- La clé `ts` a disparu du contexte des callbacks en 3.x, ce qui empêchait
  l'alerte mail de partir (issue #14).

## BigQuery Sandbox

- Le Sandbox **supprime toute partition de plus de 60 jours**, sans possibilité
  de le désactiver. **Ne jamais partitionner par date métier.** Les tables non
  partitionnées gardent tout leur historique.
- Pas de DML ni de streaming, chargement par lots uniquement.
- Les tables entières expirent aussi à 60 jours, mais `create_table(exists_ok=True)`
  les recrée : le pipeline se répare tant qu'il tourne.

Projet `crucial-bonsai-418120`, région EU, datasets `raw`, `marts_staging`,
`marts`. Clé de service dans `~/.gcp/mbda-projet2-sa.json`.

## Ordonnancement

**Un seul déclencheur planifié à la fois.** Les deux écrivent les mêmes tables
en `WRITE_TRUNCATE`, deux exécutions simultanées s'écraseraient.

- GitHub Actions, les jours ouvrés à 18h37, c'est le déclencheur actif. Il
  tourne sans machine allumée.
- Le DAG Airflow, `schedule=None`, déclenchement manuel. Sert à démontrer
  l'orchestration.

La minute décalée est volontaire : GitHub met les workflows planifiés en file
quand la charge est forte, et elle est maximale en début d'heure. Un run lancé
à 18h59 a déjà attendu 16 heures.

**Ne pas relancer la recherche d'un ordonnanceur cloud gratuit.** Elle a été
faite : GitLab exige une carte depuis 2021, Docker Hub est un registre et pas un
ordonnanceur, Cloudflare Workers coupe à 30 s, PythonAnywhere filtre le réseau,
Oracle Cloud demande une carte. La consigne n'exige aucun hébergement.

## Pièges de données

- **Yahoo, `range=max` renvoie du mensuel.** Demander `10y` pour du quotidien.
- **Certains instruments cotent en centimes** : `USX`, `GBp`, `ZAc`. `raw` garde
  la valeur brute, la division par 100 se fait dans dbt via le seed
  `mapping_devise_cotation`.
- **Les symboles sont réattribués.** Barrick cotait sous `GOLD`, puis a changé de
  nom en 2025 et est passée à `B`. `GOLD` a été repris par Gold.com, Inc., et
  Yahoo sert l'historique de cette dernière : corrélation avec l'or de 0,215 au
  lieu de 0,655. Vérifier `longName` dans la réponse de l'API avant d'ajouter ou
  de modifier un ticker. Un test le verrouille.
- **Une clôture peut être négative.** Le WTI a coté -37,63 le 20 avril 2020,
  seul cas de l'historique. `variation_pct` sort alors -306 %, ce qui n'est pas
  un rendement. La colonne `variation_exploitable` marque ces lignes ; elles
  restent dans la table et chaque agrégat publie une valeur avec et une sans.
  L'écart n'est pas anecdotique : avril 2020 passe de 12,30 à 4,74.
- **Le MRU n'existe que depuis janvier 2018.** Un filtre exigeant toutes les
  devises écartait 43 % de l'historique. `raw` reste une copie fidèle, le
  filtrage appartient à dbt.

## Conventions du modèle

- Grain de la table de faits : **un instrument, un jour**.
- **Deux tables de faits de grains incompatibles.** Ne jamais joindre
  `fct_cotation_journaliere` et `fct_exportations_pays` directement, le lien
  passe par `categorie_export`.
- **La volatilité se mesure sur `variation_pct`, jamais sur `cloture_eur`.** Un
  écart-type de prix comparerait un instrument à 2 EUR et un autre à 800 EUR.
- L'écart-type retenu partout est celui **d'échantillon** (`stddev` en BigQuery).
  C'est lui qui reproduit les chiffres publiés.
- Extraction complète à chaque exécution, `WRITE_TRUNCATE`. Dix ans font 34 Mo,
  l'incrémental n'apporterait rien et le rejeu reste sans effet de bord.
- La paire témoin Orange / Or ne mesure aucun lien réel : sa corrélation doit
  rester proche de zéro. Un test singulier échoue au-delà de 0,15. C'est elle
  qui valide toutes les autres.

## Dépôt

- Dépôt **public** : la protection de branche ne fonctionne pas sur un dépôt
  privé en plan gratuit.
- Branches nommées d'après les membres, plus des branches de travail
  ponctuelles. **Ne jamais supprimer de branche.**
- `main` est protégée et exige une review. Personne ne fusionne sa propre PR.
- Les documents du dépôt n'utilisent pas de tiret cadratin.
- Les identifiants ne sont jamais dans le code : `MBDA_SMTP_USER`,
  `MBDA_SMTP_PASSWORD`, `MBDA_SMTP_TO` pour les alertes, `MBDA_KEYFILE` pour
  BigQuery. Le mot de passe Gmail est un mot de passe d'application.
- Le callback d'alerte ne part **qu'après épuisement des relances**, soit trois
  essais toutes les 5 minutes. Une tâche en `UP_FOR_RETRY` n'a pas encore
  alerté. Pour tester vite, dupliquer le DAG avec `retries: 0` :
  `airflow tasks test` n'exécute pas les callbacks, seul `dags test` le fait.

## Vérifier avant de proposer

```bash
python -m pytest tests -q                       # logique pure
cd dbt_pipeline && dbt build                    # modèles et tests, sur BigQuery
```

Et pour le DAG, sans passer par l'interface :

```bash
export AIRFLOW_HOME=$PWD/airflow_home
export AIRFLOW__CORE__DAGS_FOLDER=$PWD/airflow/dags
export PATH=/chemin/vers/venv-airflow/bin:$PATH
airflow dags test ingest_market_data
```
