# Maquette du tableau de bord

Une page de référence à reproduire, pas un modèle à inventer. Ouvre
`tableau-de-bord.html` par double-clic : aucun serveur, aucune connexion,
aucune installation.

Elle affiche **les vraies données du projet**, pas des chiffres d'exemple. C'est
là son intérêt : elle dit à quoi chaque page doit ressembler **et** quels
chiffres doivent y apparaître.

| Fichier | À quoi il sert |
|---|---|
| `tableau-de-bord.html` | la maquette, autonome, à ouvrir directement |
| `gabarit.html` | le modèle sans les données, pour modifier la mise en page |
| `construire.py` | régénère la maquette avec les données du jour |

```bash
python docs/maquette/construire.py
```

---

## Maquette et application, deux choses différentes

La maquette est **figée** : elle contient les données du jour où elle a été
construite. L'application Streamlit, dans `dashboard/`, lit BigQuery **en
direct**.

Les chiffres peuvent donc différer légèrement entre les deux, et c'est normal :
le pipeline tourne tous les jours ouvrés et l'historique s'allonge. Un écart de
quelques centièmes est attendu. Un écart d'un ordre de grandeur, non : dans ce
cas une colonne n'est pas la bonne.

Pour les comparer sur la même base, régénérer la maquette avec `construire.py`.

---

## La règle qui simplifie tout

**Les calculs sont déjà faits.** Les six tables `agg_*` et `kpi_*` du dataset
`marts` contiennent les écarts-types, les corrélations, les classements et les
comparaisons annuelles. Il n'y a **aucune formule à écrire** dans le tableau de
bord, juste des colonnes à poser sur un graphique.

C'est volontaire : une moyenne recalculée à l'affichage donnerait un chiffre
différent de celui du rapport, et personne ne saurait lequel est bon.

**Le tableau de bord ne lit que `marts`.** Le compte de service utilisé est en
lecture seule et n'a accès ni à `raw`, ni à `marts_staging`. Si une donnée
manque, elle doit être ajoutée à une table de `marts` par la couche dbt.

---

## Ce que chaque page doit afficher

### Page 1 · Le régime de change protège-t-il de la volatilité ?

**Table** : `dim_devise` (16 lignes)

| Élément | Colonnes |
|---|---|
| Cartes | `coefficient_variation` pour XOF, puis NGN |
| Graphique | barres **horizontales**, `devise_id` en axe, `coefficient_variation` en valeur |
| Tri | croissant sur la valeur |
| Couleur | par `regime` : arrimé bleu, géré jaune, flottant orange |

Barres horizontales et non verticales : les noms de devises se lisent
normalement, et l'écart entre 0,000 et 0,72 saute aux yeux.

### Page 2 · Quelle classe d'actif est la plus volatile ?

**Table** : `agg_volatilite_classe_annee` (33 lignes)

| Élément | Colonnes |
|---|---|
| Cartes | volatilité d'ensemble par classe, **recalculée**, pas moyennée |
| Graphique | courbes, `annee` en abscisse, `volatilite` en valeur, une série par `classe_actif` |
| Bascule | `volatilite` ou `volatilite_hors_anomalie` |

Un écart-type ne se moyenne pas : la valeur d'ensemble se recalcule sur toutes
les observations, c'est ce que fait `donnees.volatilite_totale()`.

L'écart entre les deux mesures est le sujet d'un paragraphe du rapport, il ne
faut pas le cacher.

### Page 3 · Quel pays a le panier d'exportation le plus exposé ?

**Table** : `agg_exportations_evolution` (300 lignes)

| Élément | Colonnes |
|---|---|
| Graphique | barres **empilées horizontales**, `pays` en axe, `part_exportations` en valeur, `categorie_export` en série |
| Filtre | `annee` |
| Évolution | courbes par pays, `annee` en abscisse |

`est_categorie_dominante` évite de recalculer le classement, `ecart_points`
donne l'évolution par rapport à l'année précédente.

**Écrire les écarts en points, pas en pourcentage.** `part_exportations` est
déjà un pourcentage. Et **jamais de camembert** : les quatre catégories ne
totalisent pas 100 %.

### Page 4 · Les sociétés extractives suivent-elles leur matière ?

**Tables** : `agg_correlation_instrument`, `agg_correlation_paire_annee`, et
`fct_cotation_journaliere` pour les nuages.

| Élément | Colonnes |
|---|---|
| Graphique | barres horizontales, `libelle` en axe, `correlation` en valeur |
| Couleur | gris quand `temoin` est vrai, bleu sinon |
| Nuage | `variation_pct` de l'action en X, de la matière en Y |
| Stabilité | courbes de `correlation` par `annee` |

Le gris du témoin porte une information : « cette paire ne mesure rien, elle
sert de contrôle ». Ce n'est pas une décoration.

### Page 5 · Quelles ont été les périodes de tension ?

**Table** : `agg_tension_mensuelle` (121 lignes)

| Élément | Colonnes |
|---|---|
| Graphique | colonnes, `mois` en abscisse, `volatilite` en valeur |
| Couleur | rouge quand `est_tension` est vrai, bleu sinon |
| Repère | ligne horizontale à `mediane_historique` × 3 |

---

## Mise en page commune

```
┌────────────────────────────────────────────────┐
│  Titre de la question                          │
│  Une phrase qui donne la réponse               │
├────────────────────────────────────────────────┤
│  [chiffre clé]  [chiffre clé]  [chiffre clé]   │
├────────────────────────────────────────────────┤
│              graphique principal               │
├────────────────────────────────────────────────┤
│   graphique secondaire   │   graphique         │
└────────────────────────────────────────────────┘
```

**La phrase sous le titre est ce qui distingue un tableau de bord d'une
collection de graphiques.** Écrire « Les monnaies arrimées affichent une
volatilité nulle, les flottantes jusqu'à 0,72 » plutôt que « Volatilité par
devise ». Les cinq phrases sont déjà rédigées dans la maquette et dans les
modules `dashboard/questions/`.

---

## La palette

| Rôle | Couleur | Usage |
|---|---|---|
| Série 1 | `#2a78d6` | bleu, série principale |
| Série 2 | `#eb6834` | orange, série de comparaison |
| Série 3 | `#1baf7a` | vert, troisième série |
| Série 4 | `#eda100` | jaune, quatrième série |
| Neutre | `#94a3b8` | témoin, valeurs de référence |
| Alerte | `#e34948` | **uniquement** les périodes de tension |

Textes : `#1a1a19` pour les titres, `#5a6b64` pour les libellés secondaires.
Grilles et axes : `#e2e8f0`, jamais plus foncé. Les mêmes valeurs sont dans
`dashboard/style.py`.

**Une couleur suit toujours la même entité.** Si un filtre retire une série, les
autres gardent leur teinte. Ne jamais attribuer les couleurs par rang.

Le rouge est réservé à l'alerte. Ne pas l'utiliser comme cinquième couleur de
série, sinon il ne veut plus rien dire.

Cette palette a été vérifiée pour le daltonisme. Le vert et le jaune ont un
contraste faible sur fond blanc : partout où ils servent, **afficher la valeur
en étiquette** à côté de la barre, comme dans la maquette.
