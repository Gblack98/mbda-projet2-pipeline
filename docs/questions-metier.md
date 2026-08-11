# Questions métier et tableau de bord

Cinq questions, cinq pages de tableau de bord. Chaque section donne les colonnes
à utiliser, le type de graphique, et les résultats déjà mesurés pour vérifier que
la page dit vrai.

Toutes les données viennent du dataset `marts`. Ne jamais brancher un rapport sur
`marts_staging`, qui ne sert qu'à dbt.

Les agrégations sont calculées par le pipeline, pas dans l'outil de restitution.
Six tables portent les indicateurs, à brancher telles quelles :

| Table | Grain | Question |
|---|---|---|
| `agg_volatilite_classe_annee` | classe d'actif × année | 2 |
| `agg_tension_mensuelle` | mois | 5 |
| `agg_correlation_instrument` | paire société / matière | 4 |
| `agg_correlation_paire_annee` | paire × année | 4 |
| `agg_exportations_evolution` | pays × catégorie × année | 3 |
| `kpi_instrument_annee` | instrument × année | 2 et 5 |

Recalculer un écart-type dans le tableau de bord donnerait un chiffre différent
de celui du rapport. Prendre la colonne déjà calculée.

**Une convention à connaître avant de lire un chiffre.** `variation_pct` est un
rendement, et un rendement suppose deux clôtures de même signe. Le WTI a coté
-37,63 le 20 avril 2020, seule clôture négative de l'historique : le calcul sort
alors -306 % puis -127 %, deux valeurs qui ne sont pas des rendements. Ces lignes
restent dans les données, marquées par `variation_exploitable` à faux, et chaque
table d'agrégation publie deux colonnes : `volatilite` qui les inclut, et
`volatilite_hors_anomalie` qui les écarte. `observations_ecartees` dit combien il
y en avait. Toujours préciser laquelle des deux est citée.

---

## Palette commune

Quatre couleurs, dans cet ordre, jamais réattribuées d'une page à l'autre :

| Rôle | Clair | Usage |
|---|---|---|
| Série 1 | `#2a78d6` | bleu — série principale, matières premières |
| Série 2 | `#eb6834` | orange — série de comparaison, actions |
| Série 3 | `#1baf7a` | vert d'eau — troisième série, indices |
| Série 4 | `#eda100` | jaune — quatrième série |

Textes : `#1a1a19` pour les titres, `#5a6b64` pour les libellés secondaires.
Fond des cartes : blanc. Grilles et axes en `#e2e8f0`, jamais plus foncé.

Une couleur suit toujours la même entité. Si un filtre retire une série, les
autres gardent leur teinte.

---

## 1. Le régime de change protège-t-il de la volatilité ?

**Le message** : les monnaies arrimées ont une volatilité nulle, les flottantes
non. C'est la question qui porte le sujet, mets-la en première page.

**Données** : `dim_devise`

| Colonne | Rôle |
|---|---|
| `devise_id` | dimension |
| `regime` | dimension de découpage |
| `coefficient_variation` | métrique |

**Graphique** : barres horizontales, une par devise, triées par coefficient
croissant. Couleur par `regime`.

- `arrime` → `#2a78d6`
- `gere` → `#eda100`
- `flottant` → `#eb6834`
- `reference` → gris `#94a3b8`

Barres horizontales et non verticales : les noms de devises se lisent
naturellement, et l'écart entre 0,00 et 0,72 saute aux yeux.

**Résultats à retrouver**

| Devise | Coefficient | Régime |
|---|---|---|
| XOF, CVE | 0,000 | arrimé |
| MAD | 0,020 | géré |
| MRU | 0,058 | géré |
| NGN | 0,722 | flottant |

**Trois chiffres clés** à poser au-dessus du graphique : `0,000` pour le XOF,
`0,722` pour le NGN, et l'écart entre les deux.

---

## 2. Quelle classe d'actif est la plus volatile ?

**Données** : `agg_volatilite_classe_annee`, une ligne par classe et par année.

| Colonne | Rôle |
|---|---|
| `annee` | axe des abscisses |
| `classe_actif` | série |
| `volatilite` | métrique |

**Graphique** : courbes, une par classe d'actif, sur dix ans.

- Matières premières → `#2a78d6`
- Actions → `#eb6834`
- Indices → `#1baf7a`

Traits de 2 px, points de 8 px minimum. Étiqueter directement les trois courbes
en bout de ligne plutôt que par une légende séparée.

**Le piège** : la volatilité se calcule sur `variation_pct`, jamais sur
`cloture_eur`. Un écart-type des prix comparerait Kosmos à 2 € et Anglo American
à 800 €, ce qui n'a aucun sens. La colonne `volatilite` applique déjà cette
règle, il n'y a pas de champ calculé à créer.

**L'année 2020 demande une phrase d'explication.** Les matières premières y sont
à 5,21, devant les indices à 4,64 et les actions à 4,23. Mais deux observations
sur 5 819 portent tout l'écart, les deux séances du WTI à prix négatif : sans
elles la classe retombe à 2,88 et passe dernière. Citer les deux chiffres, la
colonne `volatilite_hors_anomalie` donne le second.

`kpi_instrument_annee` permet de descendre au niveau de l'instrument si un jury
demande quel actif porte la volatilité d'une classe.

---

## 3. Quel pays a le panier d'exportation le plus exposé ?

**Données** : `fct_exportations_pays`, jointe à `dim_instrument` par
`categorie_export`

| Colonne | Rôle |
|---|---|
| `pays` | dimension |
| `categorie_export` | sous-dimension |
| `part_exportations` | métrique |
| `annee` | filtre |

**Graphique** : barres empilées horizontales, une barre par pays, segments par
catégorie. Un espace de 2 px entre segments.

**Ne jamais joindre cette table à `fct_cotation_journaliere`.** Les grains sont
incompatibles (pays × catégorie × année contre instrument × jour). Le lien passe
par `categorie_export`, présent des deux côtés.

**Résultats 2024**

| Pays | Catégorie dominante | Part |
|---|---|---|
| Mauritanie | Métaux | 33,7 % |
| Sénégal | Énergie | 32,7 % |
| Sénégal | Alimentaire | 21,6 % |

Ajouter un filtre sur `annee` pour montrer l'évolution 2015-2024.

Pour la comparaison dans le temps, prendre `agg_exportations_evolution` plutôt
que la table de faits : elle porte `ecart_points`, l'écart avec l'année
précédente, et `annee_precedente`, qui dit sur quelle année porte la
comparaison. La Banque Mondiale laisse des trous selon les pays, l'année
précédente n'est donc pas toujours celle d'avant. `est_categorie_dominante`
évite de recalculer le classement dans l'outil.

`part_exportations` est déjà un pourcentage : un écart se lit **en points**, pas
en pourcentage. Écrire « l'énergie gagne 4,2 points » et non « gagne 4,2 % ».

---

## 4. Les sociétés extractives suivent-elles leur matière ?

**Données** : `fct_cotation_journaliere`, deux instruments comparés

**Graphique** : nuage de points. Variation quotidienne de l'action en abscisse,
variation de la matière en ordonnée. Un point par jour.

Ajouter une droite de tendance. Plus les points s'alignent, plus la société suit
son sous-jacent.

**Corrélations mesurées**, table `agg_correlation_instrument`, treize paires
définies dans le seed `paires_instrument`.

| Paire | r |
|---|---|
| Barrick / Or | 0,655 |
| Newmont / Or | 0,624 |
| Kinross / Or | 0,618 |
| Endeavour / Or | 0,546 |
| Exxon / Brent | 0,534 |
| BP / Brent | 0,528 |
| Woodside / Brent | 0,504 |
| Shell / Brent | 0,482 |
| Glencore / Cuivre | 0,480 |
| TotalEnergies / Brent | 0,471 |
| Anglo American / Cuivre | 0,455 |
| Kosmos / Gaz | 0,087 |
| **Orange / Or (témoin)** | **0,043** |

Le classement se lit tout seul : les trois plus gros producteurs d'or occupent
les trois premières places, les pétrolières suivent entre 0,47 et 0,53, les
diversifiées du cuivre viennent après, et le témoin ferme la marche.

Le témoin est ce qui rend la page convaincante. Orange n'a aucun rapport avec
l'or, et sa corrélation est nulle : les 0,6 des sociétés minières ne sont donc
pas un artefact. Un test dbt échoue si ce témoin dépasse 0,15, ce qui protège
la démonstration d'une erreur de calcul introduite plus tard.

**Le cas Barrick mérite d'être raconté dans le rapport.** Une version
précédente donnait Barrick à 0,215, en bas du tableau, et l'expliquait par la
diversification de la société. C'était faux. Le découpage par année, table
`agg_correlation_paire_annee`, montrait un coefficient bloqué autour de 0,1
pendant six ans quand Kinross et Newmont tenaient 0,5 à 0,7 : un pur minier
aurifère ne fait pas ça.

En cause, le ticker. Barrick cotait sous `GOLD` jusqu'à son changement de nom
en 2025, puis est passée à `B`. Le symbole `GOLD` a été repris par Gold.com,
Inc., une autre société, et l'API renvoie l'historique de cette dernière. Le
champ `longName` de Yahoo le dit noir sur blanc. Avec le bon ticker, Barrick
passe de 0,215 à **0,655**, en tête du tableau, ce qui est la place attendue du
deuxième producteur mondial.

C'est un bon exemple à citer : la donnée était disponible, le pipeline
fonctionnait, les tests passaient, et le chiffre était faux quand même. C'est
la comparaison entre sociétés comparables qui a fait apparaître l'anomalie.

Kosmos à 0,087 s'explique autrement, et cette fois vraiment : la société
exploite du gaz qui ne se vend pas au prix de la référence américaine.

**Mise en page** : une grille de six nuages de points côte à côte, même échelle
partout, plutôt qu'un seul graphique avec un sélecteur.

---

## 5. Quelles ont été les périodes de tension ?

**Données** : `agg_tension_mensuelle`, une ligne par mois.

**Graphique** : histogramme mensuel de `volatilite`, sur dix ans. Une seule
série, en `#2a78d6`. Colorer en `#e34948` les mois où `est_tension` vaut vrai,
c'est-à-dire au-delà de trois fois la médiane des mois observés. La médiane est
dans `mediane_historique`, le rapport à celle-ci dans `multiple_mediane`.

**Résultats**

| Mois | Volatilité | Hors anomalie | Tension |
|---|---|---|---|
| 2020-04 | 12,30 | 4,74 | oui |
| 2020-03 | 7,17 | 7,17 | oui |
| 2018-02 | 4,91 | 4,91 | non |
| 2025-04 | 4,28 | 4,28 | non |

Deux mois seulement dépassent le seuil, tous les deux au premier trimestre 2020.
La médiane historique est à 2,34.

**Ce que dit vraiment le pic d'avril 2020.** Il tient à deux observations sur
853, les deux séances du WTI à prix négatif. Sans elles le mois retombe à 4,74,
donc derrière mars 2020. Le mois le plus agité du krach est mars, pas avril.
Avril est le mois de l'anomalie de prix. Les deux faits sont réels et méritent
chacun une annotation, mais ce ne sont pas les mêmes.

Sous le graphique, un second visuel : la volatilité par classe d'actif pendant
mars et avril 2020.

| Classe | Volatilité | Hors anomalie |
|---|---|---|
| Matières premières | 11,65 | 5,02 |
| Actions | 7,43 | 7,43 |
| Indices | 7,02 | 7,02 |

Le classement s'inverse selon la colonne retenue : les matières premières sont
soit la classe la plus agitée, soit la plus calme. Dire laquelle des deux
colonnes est affichée, sinon le graphique se contredit d'une lecture à l'autre.

---

## Construire les pages

Le tableau de bord est une application Streamlit, dans `dashboard/`. Elle lit
directement le dataset `marts` avec un compte de service en lecture seule.

```bash
./venv-dashboard/bin/streamlit run dashboard/app.py
```

Un fichier par question, dans `dashboard/questions/`. Chacun expose son titre,
sa phrase de réponse, et une fonction `rendre()` qui pose les métriques et les
graphiques. **`docs/guide-dashboard.md` détaille tout, pas à pas.**

**Aucun calcul n'est à écrire.** Les six tables d'agrégation portent déjà les
écarts-types, les corrélations, les classements et les comparaisons annuelles.
Une page ne fait que choisir des colonnes et un type de graphique.

**Aucun SQL non plus.** Tout passe par `dashboard/donnees.py`, une fonction par
table, qui rend un DataFrame. Si une donnée manque, on ajoute une fonction là,
pas une requête dans une page.

Les filtres sont dans le volet de gauche et s'appliquent à la page entière :
période, classe d'actif, mesure. C'est ce qui fait la différence entre un
tableau de bord et une suite de graphiques : on doit pouvoir découper les
mesures par les axes du modèle en étoile.

## Mise en page commune

Cinq pages, une par question. Sur chaque page :

```
┌────────────────────────────────────────────────┐
│  Titre de la question                          │
│  Une phrase qui donne la réponse               │
├────────────────────────────────────────────────┤
│  [chiffre clé]  [chiffre clé]  [chiffre clé]   │
├────────────────────────────────────────────────┤
│                                                │
│              graphique principal               │
│                                                │
├────────────────────────────────────────────────┤
│   graphique secondaire   │   filtres           │
└────────────────────────────────────────────────┘
```

La phrase sous le titre est ce qui distingue un tableau de bord d'une collection
de graphiques. Écrire « Les monnaies arrimées affichent une volatilité nulle,
les flottantes jusqu'à 0,72 » plutôt que « Volatilité par devise ».
