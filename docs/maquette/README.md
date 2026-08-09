# Maquette du tableau de bord

Une page à reproduire, pas un modèle à inventer. Ouvre `tableau-de-bord.html`
par double-clic : aucun serveur, aucune connexion, aucune installation.

Elle affiche **les vraies données du projet**, pas des chiffres d'exemple. Les
valeurs qu'on y lit sont celles qui doivent apparaître dans l'outil final. Si un
chiffre diffère, c'est que quelque chose n'est pas branché au bon endroit.

| Fichier | À quoi il sert |
|---|---|
| `tableau-de-bord.html` | la maquette, autonome, à ouvrir directement |
| `gabarit.html` | le modèle sans les données, pour modifier la mise en page |
| `construire.py` | régénère la maquette avec les données du jour |
| `theme-powerbi.json` | le thème à importer dans Power BI |

Pour régénérer après une nouvelle exécution du pipeline :

```bash
python docs/maquette/construire.py
```

---

## La règle qui simplifie tout

**Les calculs sont déjà faits.** Les six tables `agg_*` et `kpi_*` du dataset
`marts` contiennent les écarts-types, les corrélations, les classements et les
comparaisons annuelles. Il n'y a **aucune formule à écrire** dans Looker ou
Power BI, juste des colonnes à poser sur un graphique.

C'est volontaire : une moyenne recalculée dans l'outil de restitution donnerait
un chiffre différent de celui du rapport, et personne ne saurait lequel est bon.

**Ne jamais brancher un rapport sur `marts_staging`.** Ce dataset ne sert qu'à
dbt. Tout ce qui est utile est dans `marts`.

---

## Ce qu'il faut brancher, page par page

Une page par question. Pour chaque graphique : la table, les colonnes, le type
de visuel.

### Page 1 · Le régime de change protège-t-il de la volatilité ?

**Table** : `dim_devise` (16 lignes)

| Élément | Comment |
|---|---|
| Trois cartes en haut | `coefficient_variation` filtré sur XOF, puis NGN |
| Graphique principal | barres **horizontales**, une par devise |
| Axe | `devise_id` · Valeur | `coefficient_variation` |
| Tri | croissant sur la valeur |
| Couleur | par `regime` : arrimé bleu, géré jaune, flottant orange |

Barres horizontales et non verticales : les noms de devises se lisent
normalement, et l'écart entre 0,000 et 0,721 saute aux yeux.

### Page 2 · Quelle classe d'actif est la plus volatile ?

**Table** : `agg_volatilite_classe_annee` (33 lignes)

| Élément | Comment |
|---|---|
| Cartes | `volatilite`, une par `classe_actif`, toutes années |
| Graphique principal | **courbes**, une par classe |
| Axe | `annee` · Valeur | `volatilite` · Légende | `classe_actif` |
| Filtre | un segment sur `classe_actif` |

Poser aussi `volatilite_hors_anomalie` en second graphique, ou en bouton de
bascule si l'outil le permet. **L'écart entre les deux est le sujet d'un
paragraphe du rapport**, il ne faut pas le cacher.

### Page 3 · Quel pays a le panier d'exportation le plus exposé ?

**Table** : `agg_exportations_evolution` (300 lignes)

| Élément | Comment |
|---|---|
| Graphique principal | barres **empilées horizontales** |
| Axe | `pays` · Valeur | `part_exportations` · Légende | `categorie_export` |
| Filtre | `annee`, réglé sur 2024 par défaut |
| Deux graphiques du bas | courbes, `annee` en axe, un pays chacun |

`est_categorie_dominante` évite de recalculer le classement, et `ecart_points`
donne l'évolution par rapport à l'année précédente.

**Écrire les écarts en points, pas en pourcentage.** `part_exportations` est déjà
un pourcentage : « l'énergie gagne 13 points » et non « gagne 13 % ».

### Page 4 · Les sociétés extractives suivent-elles leur matière ?

**Tables** : `agg_correlation_instrument` (13 lignes) et
`fct_cotation_journaliere` pour les nuages.

| Élément | Comment |
|---|---|
| Graphique principal | barres horizontales, `libelle` en axe, `correlation` en valeur |
| Couleur | gris pour la ligne où `temoin` est vrai, bleu pour les autres |
| Nuages de points | six petits graphiques côte à côte, **même échelle partout** |

Pour un nuage : filtrer `fct_cotation_journaliere` sur deux `instrument_id`,
mettre `variation_pct` de l'action en X et celui de la matière en Y, un point par
`date_cotation`, et ajouter une droite de tendance.

Six graphiques identiques valent mieux qu'un seul avec un sélecteur : on compare
d'un coup d'œil.

### Page 5 · Quelles ont été les périodes de tension ?

**Table** : `agg_tension_mensuelle` (121 lignes)

| Élément | Comment |
|---|---|
| Graphique principal | **colonnes**, une par mois |
| Axe | `mois` · Valeur | `volatilite` |
| Couleur | rouge `#e34948` quand `est_tension` est vrai, bleu sinon |
| Ligne de référence | à `mediane_historique` × 3 |

`multiple_mediane` dit de combien un mois dépasse la normale, utile en infobulle.

---

## Power BI

**Le thème d'abord.** *Affichage* → *Thèmes* → *Parcourir les thèmes*, choisir
`theme-powerbi.json`. Il applique la palette, retire les ombres et les bordures
épaisses, met les grilles en gris clair et aligne les titres à gauche. Tout le
reste hérite ensuite automatiquement.

**La connexion.** *Obtenir les données* → *Google BigQuery* → connexion avec le
compte Google qui a accès au projet `crucial-bonsai-418120`. Choisir le dataset
`marts`, cocher les tables voulues.

Prendre le mode **Import** et non DirectQuery : le volume est minuscule, moins de
10 Mo, et le rapport sera bien plus réactif.

Si la connexion directe pose problème, exporter les tables en CSV depuis la
console BigQuery et les importer. C'est moins élégant mais ça débloque.

**Le modèle.** Dans la vue *Modèle*, relier `fct_cotation_journaliere` aux trois
dimensions : `instrument_id` vers `dim_instrument`, `date_cotation` vers
`dim_temps.date_jour`, `devise_pivot` vers `dim_devise.devise_id`. Cardinalité
plusieurs-à-un, sens de filtre simple.

**Ne pas relier les deux tables de faits entre elles.** Leurs grains sont
incompatibles, Power BI produirait des totaux faux sans prévenir.

Les tables `agg_*` n'ont besoin d'aucune relation : elles se suffisent.

**Aucune mesure DAX n'est nécessaire.** Si tu veux quand même un total propre sur
une carte, utiliser `Moyenne` et jamais `Somme` sur une colonne de volatilité :
additionner des écarts-types n'a aucun sens.

**Attention** : Power BI Desktop ne fonctionne pas sous Linux. Sur Linux, faire
le rapport dans Looker Studio.

---

## Looker Studio

**La connexion.** `lookerstudio.google.com` → *Créer* → *Rapport* → connecteur
**BigQuery** → projet `crucial-bonsai-418120` → dataset `marts`. Ajouter une
source par table utilisée.

**Les couleurs.** *Thème et mise en page* → *Personnaliser* → coller les quatre
couleurs dans l'ordre : `#2a78d6`, `#eb6834`, `#1baf7a`, `#eda100`. Puis, dans
*Style*, décocher les bordures et les ombres des graphiques.

Pour colorer par régime ou marquer les mois de tension, utiliser
*Style* → *Couleurs par valeur de dimension* et fixer une couleur par valeur.

**Les jointures.** *Ressource* → *Gérer les sources* → *Fusionner les données*.
Joindre `fct_cotation_journaliere` à `dim_instrument` sur `instrument_id`, et à
`dim_temps` sur `date_cotation = date_jour`. Type *Left outer*.

Les tables `agg_*` ne demandent aucune fusion.

**Un point de vigilance.** Looker Studio agrège par défaut en *Somme*. Sur une
colonne de volatilité ou de corrélation, il faut passer l'agrégation à
**Moyenne** ou à **Aucune**, sinon le graphique additionne des valeurs qui ne
s'additionnent pas. C'est l'erreur la plus fréquente.

**Un filtre de dates commun** en haut de chaque page, appliqué au rapport entier.

---

## Mise en page commune

Chaque page suit la même structure :

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
volatilité nulle, les flottantes jusqu'à 0,721 » plutôt que « Volatilité par
devise ». Les cinq phrases sont déjà rédigées dans la maquette, il suffit de les
recopier.

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
Grilles et axes : `#e2e8f0`, jamais plus foncé.

**Une couleur suit toujours la même entité.** Si un filtre retire une série, les
autres gardent leur teinte. Ne jamais attribuer les couleurs par rang.

Le rouge est réservé à l'alerte. Ne pas l'utiliser comme cinquième couleur de
série, sinon il ne veut plus rien dire.

Cette palette a été vérifiée pour le daltonisme. Le vert et le jaune ont un
contraste faible sur fond blanc : partout où ils servent, **afficher la valeur en
étiquette** à côté de la barre, comme dans la maquette.

---

## Si quelque chose bloque

**Un chiffre ne correspond pas à la maquette.** Vérifier l'agrégation du champ.
Une somme là où il faut une moyenne est la cause la plus fréquente.

**Les données paraissent vides.** Le pipeline n'a peut-être pas tourné
récemment. Le mode Sandbox de BigQuery supprime les tables 60 jours après leur
création. Relancer le pipeline et recharger la source.

**Un total dépasse 100 % dans les exportations.** Normal : les quatre catégories
ne couvrent pas la totalité des exportations, et elles ne s'additionnent pas à
100. Ne pas afficher de camembert avec ces données.
