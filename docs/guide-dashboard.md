# Guide du tableau de bord

Ce guide sert à construire les cinq pages du tableau de bord, pas à pas.

La partie technique ingrate est déjà faite : la connexion à BigQuery, le compte
de service, les droits, le cache, la coquille de l'application et les filtres.
Il reste la partie intéressante, celle qui demande du jugement : choisir le bon
graphique, la bonne couleur, la bonne phrase.

---

## 1. Démarrer

```bash
python -m venv venv-dashboard
./venv-dashboard/bin/pip install -r requirements-dashboard.txt
./venv-dashboard/bin/streamlit run dashboard/app.py
```

Puis `http://localhost:8501`.

À chaque fois qu'un fichier est enregistré, Streamlit propose de recharger la
page. On travaille sans jamais relancer la commande, le retour est immédiat.

**La clé de connexion** n'est pas dans le dépôt, c'est volontaire. Elle est
attendue à `~/.gcp/mbda-dashboard-ro.json`, ou dans la variable
`MBDA_DASHBOARD_KEYFILE`. Se la faire transmettre directement, jamais par le
dépôt ni par un canal public.

Pour vérifier que tout est branché :

```bash
./venv-dashboard/bin/python dashboard/donnees.py
```

Cela affiche le compte utilisé, une lecture qui passe, et une qui est refusée.

---

## 2. Ce qui est déjà en place

### Le compte de service

`mbda-dashboard-ro`, **en lecture seule**, limité au dataset `marts`. Il ne peut
ni écrire, ni lire `raw`, ni lire `marts_staging`.

C'est délibéré et ça vaut d'être expliqué dans le rapport : un tableau de bord
n'a aucune raison d'avoir plus de droits que la lecture des tables finales. Si
une erreur de code partait en boucle, elle ne pourrait rien casser.

Conséquence pratique : une erreur `403` sur `raw` n'est pas un bug à contourner.
Si une donnée manque, elle doit être ajoutée à une table de `marts` par la
couche dbt.

### L'accès aux données

Tout passe par `dashboard/donnees.py`. Une fonction par table, qui rend un
DataFrame pandas déjà en cache.

```python
import donnees

d = donnees.devises()        # DataFrame prêt à l'emploi
```

**Ne pas écrire de SQL dans une page.** Si une donnée manque, ajouter une
fonction dans `donnees.py`, sur le modèle des autres. Ça garde un seul endroit
qui parle à l'entrepôt, et le cache s'applique automatiquement.

Le cache dure dix minutes. Le bouton *Rafraîchir les données*, en bas du volet
de gauche, le vide.

### La coquille

`dashboard/app.py` tient la navigation et les filtres. Il n'y a normalement pas
à y toucher.

Chaque page est un fichier dans `dashboard/questions/` et expose trois choses :

```python
TITRE = "La question, telle qu'elle s'affiche"
REPONSE = "Une phrase qui donne la réponse"
FILTRES = ["annees", "classes", "mesure"]   # facultatif

def rendre(filtres):
    ...   # c'est ici qu'on travaille
```

Les cinq fichiers existent déjà et chargent leurs données. Ils affichent un
tableau brut en attendant les graphiques.

---

## 3. Les tables à utiliser

Onze tables dans `marts`. Cinq forment le modèle en étoile, six portent les
agrégats.

**La règle qui change tout : aucun calcul n'est à écrire.** Les écarts-types,
les corrélations, les classements et les comparaisons annuelles sont déjà
calculés par la couche dbt. Une page choisit des colonnes et un type de
graphique, rien de plus.

Si on se surprend à écrire une moyenne ou un écart-type en Python, s'arrêter :
la valeur existe déjà, et la recalculer donnerait un chiffre différent de celui
du rapport.

### Les tables d'agrégation

| Fonction | Table | Grain | Pour la question |
|---|---|---|---|
| `donnees.devises()` | `dim_devise` | une devise | 1 |
| `donnees.volatilite_classe()` | `agg_volatilite_classe_annee` | classe × année | 2 |
| `donnees.volatilite_totale()` | recalcul sur les faits | classe | 2 |
| `donnees.exportations()` | `agg_exportations_evolution` | pays × catégorie × année | 3 |
| `donnees.correlations()` | `agg_correlation_instrument` | une paire | 4 |
| `donnees.correlations_par_annee()` | `agg_correlation_paire_annee` | paire × année | 4 |
| `donnees.variations_paire(a, m)` | les faits, appariés | une séance | 4 |
| `donnees.tension()` | `agg_tension_mensuelle` | un mois | 5 |
| `donnees.kpi_instrument()` | `kpi_instrument_annee` | instrument × année | 2 et 5 |
| `donnees.instruments()` | `dim_instrument` | un instrument | filtres |
| `donnees.couverture()` | les faits | une ligne | bandeau |

### Deux colonnes à ne pas confondre

Presque toutes les tables d'agrégation ont **deux mesures côte à côte** :

- `volatilite` : toutes les observations
- `volatilite_hors_anomalie` : sans les variations inexploitables

L'écart vient d'un fait réel. Le 20 avril 2020, le pétrole a coté à prix
négatif. Or une variation en pourcentage n'a de sens qu'entre deux prix de même
signe : le calcul sort -306 % ce jour-là. Deux lignes sur 103 000, et elles
suffisent à faire passer avril 2020 de 12,3 à 4,7.

**Toujours dire laquelle des deux on affiche.** C'est pour ça que le filtre
« Mesure » existe dans le volet de gauche : il bascule de l'une à l'autre et
c'est un très bon moment de démonstration.

`observations_ecartees` dit combien de lignes sont concernées.

---

## 4. Les principes de conception

Cinq règles. Elles ne sont pas des goûts, elles se justifient.

### Choisir la forme avant la couleur

La question à se poser en premier : **qu'est-ce que le graphique doit faire
comprendre ?**

| Ce qu'on montre | Forme |
|---|---|
| Comparer des grandeurs entre catégories | barres |
| Comparer des noms longs | barres **horizontales** |
| Une évolution dans le temps | courbes |
| Une composition | barres empilées |
| Un lien entre deux mesures | nuage de points |
| **Un seul chiffre qui porte le message** | **pas de graphique, une carte** |

La dernière ligne est la plus souvent oubliée. Un graphique à une seule barre
n'est pas un graphique, c'est un chiffre déguisé.

### La palette, et pourquoi elle est fermée

Elle est dans `dashboard/style.py` :

| Rôle | Couleur | Usage |
|---|---|---|
| Série 1 | `#2a78d6` | bleu, série principale |
| Série 2 | `#eb6834` | orange, comparaison |
| Série 3 | `#1baf7a` | vert, troisième série |
| Série 4 | `#eda100` | jaune, quatrième série |
| Neutre | `#94a3b8` | témoin, référence |
| Alerte | `#e34948` | **uniquement** les périodes de tension |

Elle a été vérifiée pour le daltonisme : les couleurs restent distinguables pour
les formes courantes. L'élargir au hasard casserait cette propriété.

Trois règles qui vont avec :

**Une couleur suit une entité, jamais un rang.** Si un filtre retire une série,
les autres gardent leur teinte. Colorer « le plus grand en foncé » double une
information que la longueur de la barre donne déjà, et rend le graphique
illisible dès qu'on filtre.

**Le rouge est un statut, pas une série.** Il dit « attention ici ». S'en servir
comme cinquième couleur lui enlève tout sens.

**Le vert et le jaune ont un contraste faible sur fond blanc.** Partout où ils
servent, afficher la valeur en étiquette à côté de la barre.

### Des marques fines, une grille discrète

Traits de 2 pixels, points d'au moins 8 pixels, grille dans un gris à peine
plus foncé que le fond, pas de bordure autour des barres. Un graphique qui crie
paraît amateur.

`style.py` fournit `habiller(fig)` qui applique tout ça d'un coup :

```python
import plotly.graph_objects as go
import style as s

fig = go.Figure()
fig.add_bar(x=d["annee"], y=d["volatilite"], marker_color=s.BLEU)
st.plotly_chart(s.habiller(fig, hauteur=380), width="stretch")
```

**Appeler `habiller()` sur chaque figure.** C'est ce qui fait que les cinq pages
se ressemblent.

### Étiqueter avec parcimonie

Un chiffre sur chaque point, c'est illisible et personne ne le lit. Étiqueter
le point qui compte : le maximum, le dernier, celui qui porte le message. L'axe
et l'infobulle font le reste.

### Ce qu'il ne faut jamais faire

- **Deux axes verticaux** sur un même graphique. L'alignement des deux échelles
  est arbitraire, il invente une corrélation qui n'existe pas. Deux mesures
  d'échelles différentes, ce sont deux graphiques.
- **Un camembert** pour les exportations : les quatre catégories ne totalisent
  pas 100 %.
- **Un arc-en-ciel** pour une grandeur. Une grandeur, c'est une seule teinte du
  clair au foncé.
- **Une infobulle comme seul moyen de lire une valeur.** Il faut toujours un
  autre chemin : étiquette, axe, ou tableau dépliable.

---

## 5. Rendre le tableau de bord vivant

Un tableau de bord se distingue d'une suite de graphiques par deux choses : il
répond à une question, et il se laisse interroger.

### Les filtres

Ils sont déjà dans `app.py`, dans le volet de gauche, et s'appliquent à la page
entière. Une page déclare ceux qu'elle utilise :

```python
FILTRES = ["annees", "classes", "mesure"]
```

| Nom | Ce qu'il donne dans `filtres` |
|---|---|
| `annees` | un couple `(début, fin)` |
| `classes` | une liste de classes d'actif |
| `mesure` | `filtres["hors_anomalie"]`, vrai ou faux |
| `annee_export` | une année |

**Ne jamais mettre un filtre dans une carte de graphique.** Tout ce qui filtre
plusieurs visuels va au même endroit, en haut ou sur le côté.

Ces filtres portent sur les **dimensions** du modèle en étoile : le temps, la
classe d'actif, le pays. C'est exactement ce qu'un modèle dimensionnel sert à
faire, et c'est le point que le module évalue. Un tableau de bord figé
n'exploite pas le travail de modélisation.

### La structure d'une page

```
Titre de la question
Une phrase qui donne la réponse
────────────────────────────────
[chiffre clé] [chiffre clé] [chiffre clé]
────────────────────────────────
        graphique principal
────────────────────────────────
graphique secondaire │ commentaire
```

**La phrase sous le titre est ce qui fait la différence.** Écrire « Les monnaies
arrimées affichent une volatilité nulle, les flottantes jusqu'à 0,72 » plutôt
que « Volatilité par devise ». Un lecteur pressé doit comprendre sans regarder
le graphique.

Les briques Streamlit utiles :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Franc CFA", "0,000", help="Une seule valeur sur dix ans")

st.markdown("## Titre de section")
st.caption("La précision méthodologique qui évite un contresens.")

with st.expander("Voir les données"):
    st.dataframe(d, width="stretch", hide_index=True)
```

Le tableau dépliable n'est pas un détail : c'est ce qui permet de lire une
valeur exacte sans survoler, et de vérifier un chiffre du rapport en direct.

---

## 6. Les cinq questions

Pour chacune : la table, les colonnes, la forme recommandée et pourquoi.

La maquette `docs/maquette/tableau-de-bord.html` s'ouvre par double-clic et
montre un rendu possible, avec les chiffres attendus. C'est une référence, pas
une contrainte : faire mieux est encouragé.

---

### Question 1 · Le régime de change protège-t-il de la volatilité ?

**Réponse : oui, et l'écart est total.**

**Données** : `donnees.devises()`

| Colonne | Rôle |
|---|---|
| `devise_id`, `nom_devise` | l'identité |
| `coefficient_variation` | la mesure |
| `regime` | arrimé, géré, flottant, référence |

**Forme** : barres **horizontales**, une par devise, triées par coefficient
croissant, colorées par régime.

Horizontales parce que les noms de devises se lisent alors normalement, sans
tourner la tête. Triées parce que le classement *est* le message.

**Chiffres clés** : le franc CFA à 0,000 et le naira à 0,72. L'écart entre les
deux est spectaculaire et se passe de commentaire.

**Écarter la ligne `reference`** : c'est l'euro, qui sert de base et n'a donc
pas de taux face à lui-même.

**Une précision à afficher** : le coefficient mesure la variabilité face à
l'euro, pas une politique monétaire. Il classe le dollar en « géré » alors
qu'il flotte librement, simplement parce qu'il bouge peu face à l'euro. Le dire
vaut mieux que de le laisser trouver.

---

### Question 2 · Quelle classe d'actif est la plus volatile ?

**Réponse : les indices, parce que le VIX en fait partie.**

**Données** : `donnees.volatilite_classe()` pour l'évolution,
`donnees.volatilite_totale()` pour les chiffres d'ensemble.

| Colonne | Rôle |
|---|---|
| `annee` | l'axe du temps |
| `classe_actif` | la série |
| `volatilite` / `volatilite_hors_anomalie` | la mesure |

**Forme** : courbes, une par classe, sur dix ans.

**Attention à une erreur facile** : la volatilité d'ensemble n'est **pas** la
moyenne des volatilités annuelles. Un écart-type ne se moyenne pas. C'est
pourquoi `volatilite_totale()` existe et la recalcule sur toutes les
observations. Utiliser celle-là pour les cartes du haut.

**Le moment fort de la page** : brancher le filtre « Mesure » et regarder la
courbe des matières premières s'effondrer en 2020 quand on écarte l'anomalie.
Elle passe de première à dernière. C'est une démonstration en un clic.

**Une explication à donner** : les indices dominent parce que le VIX est dedans,
et le VIX est l'indice de la volatilité elle-même. Sans lui, les indices
seraient les plus calmes des trois classes.

---

### Question 3 · Quel pays a le panier d'exportation le plus exposé ?

**Réponse : le Nigeria, avec 88,6 % d'énergie en 2024.**

**Données** : `donnees.exportations()`

| Colonne | Rôle |
|---|---|
| `pays`, `categorie_export` | les axes |
| `part_exportations` | la mesure |
| `annee` | le filtre |
| `est_categorie_dominante` | la catégorie n°1 du pays, déjà calculée |
| `ecart_points` | l'évolution par rapport à l'année précédente |

**Forme** : barres **empilées horizontales**, une barre par pays, un segment par
catégorie, triées par total décroissant. Puis, en dessous, des courbes pour
suivre l'évolution d'un pays sur dix ans.

**Deux pièges** :

Le total ne fait pas 100 %. Les quatre catégories ne couvrent pas toutes les
exportations. Donc **pas de camembert**, et ne pas écrire « le reste ».

`part_exportations` est déjà un pourcentage, donc un écart se lit **en points**.
Écrire « l'énergie gagne 13 points » et non « gagne 13 % ». C'est l'erreur la
plus fréquente sur ce type de donnée.

**Un cas parlant** : le Sénégal passe de 19,7 % à 32,7 % d'énergie entre 2023 et
2024, avec la mise en production du champ de Sangomar. Une annotation sur la
courbe rend le graphique vivant.

---

### Question 4 · Les sociétés extractives suivent-elles leur matière ?

**Réponse : oui, et le classement se lit tout seul.**

**Données** : `donnees.correlations()`, `donnees.correlations_par_annee()`,
et `donnees.variations_paire(action, matiere)` pour les nuages.

| Colonne | Rôle |
|---|---|
| `libelle` | le nom de la paire |
| `correlation` | la mesure, entre -1 et 1 |
| `temoin` | vrai pour la paire de contrôle |
| `jours_communs` | le nombre de séances comparées |

**Forme** : barres horizontales pour le classement, puis des nuages de points.

**Le témoin est le cœur de la page.** Une paire ne mesure aucun lien réel : une
société sans rapport avec l'or, comparée à l'or. Sa corrélation doit rester
proche de zéro, et elle vaut 0,04. C'est elle qui prouve que les 0,6 des
minières ne sont pas un artefact de calcul.

La colorer en **gris**, pas en couleur de série. Le gris dit « cette ligne ne
mesure rien, elle sert de contrôle ». La couleur porte ici une information.

**Les nuages** : la variation de l'action en abscisse, celle de la matière en
ordonnée, un point par séance, plus une droite de tendance. Mettre **la même
échelle partout**, sinon la comparaison est trompeuse.

Une grille de six petits nuages côte à côte vaut mieux qu'un seul avec un
sélecteur : on compare d'un coup d'œil. Le contraste entre une paire à 0,65,
une diagonale nette, et le témoin à 0,04, un rond sans direction, est ce qui
rend la page convaincante.

**Le découpage par année** sert de contrôle de stabilité. Une paire solide garde
un coefficient régulier. C'est ce graphique qui a révélé qu'un ticker ne
renvoyait pas la société attendue.

---

### Question 5 · Quelles ont été les périodes de tension ?

**Réponse : deux mois seulement, tous les deux au premier trimestre 2020.**

**Données** : `donnees.tension()`

| Colonne | Rôle |
|---|---|
| `mois` | l'axe du temps |
| `volatilite` / `volatilite_hors_anomalie` | la mesure |
| `est_tension` | au-delà de trois fois la médiane |
| `mediane_historique`, `multiple_mediane` | le repère |

**Forme** : colonnes, une par mois, sur dix ans. En rouge les mois où
`est_tension` est vrai, plus une ligne horizontale au seuil.

Le seuil est **relatif aux données**, pas fixé à la main : trois fois la médiane
des mois observés. Il suit donc l'historique quand il s'allonge. C'est un choix
défendable à expliquer.

**La subtilité de la page** : avec toutes les observations, avril 2020 est le
mois record. Sans les deux séances de prix négatif, il repasse derrière mars.
Autrement dit, **mars est le mois du krach, avril est le mois de l'anomalie de
prix**. Ce sont deux faits différents et le graphique doit permettre de le voir,
d'où le filtre « Mesure ».

---

## 7. Avant de considérer une page finie

- [ ] Le titre est la question, pas un nom de mesure
- [ ] Une phrase sous le titre donne la réponse
- [ ] Deux ou trois chiffres clés en haut
- [ ] `habiller()` est appelé sur chaque figure
- [ ] Aucune couleur hors de la palette, le rouge seulement pour l'alerte
- [ ] Les étiquettes sont sélectives, pas une par point
- [ ] Une légende dès qu'il y a deux séries ou plus
- [ ] Un tableau dépliable donne les valeurs exactes
- [ ] Les filtres du volet de gauche changent bien le graphique
- [ ] Il est dit laquelle des deux mesures est affichée
- [ ] Les chiffres correspondent à la maquette, aux centièmes près

Le dernier point mérite une nuance : la maquette est figée au jour où elle a été
construite, l'application lit BigQuery en direct. Un écart de quelques centièmes
est normal, le pipeline tourne tous les jours ouvrés. Un écart d'un ordre de
grandeur signale une colonne mal choisie.

---

## 8. Mettre en ligne

Sur [share.streamlit.io](https://share.streamlit.io) : connecter le dépôt,
pointer `dashboard/app.py`, et coller la clé dans *Settings* → *Secrets* :

```toml
[gcp_service_account]
type = "service_account"
project_id = "crucial-bonsai-418120"
private_key_id = "…"
private_key = "-----BEGIN PRIVATE KEY-----\n…\n-----END PRIVATE KEY-----\n"
client_email = "mbda-dashboard-ro@crucial-bonsai-418120.iam.gserviceaccount.com"
client_id = "…"
token_uri = "https://oauth2.googleapis.com/token"
```

L'hébergement est gratuit et ne demande pas de carte bancaire. L'application
lira les mêmes tables, en lecture seule.

---

## 9. Si ça bloque

**« Aucun identifiant trouvé »** — la clé n'est pas là où l'application la
cherche. Voir la section 1.

**Les chiffres semblent figés** — le cache dure dix minutes. Bouton *Rafraîchir
les données* en bas du volet de gauche.

**Une erreur 403 sur `raw` ou `marts_staging`** — c'est voulu, le compte ne lit
que `marts`. La donnée manquante doit être ajoutée côté dbt.

**Un chiffre ne correspond pas** — vérifier la colonne. `volatilite` et
`volatilite_hors_anomalie` sont côte à côte et ne disent pas la même chose.

**Le graphique est vide après un filtre** — le filtre a peut-être tout écarté.
Afficher un message plutôt qu'un cadre blanc :

```python
if d.empty:
    st.warning("Aucune donnée pour cette sélection.")
    return
```
