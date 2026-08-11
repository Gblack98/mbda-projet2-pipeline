# Le tableau de bord

Application Streamlit qui lit directement BigQuery. Cinq pages, une par question
métier.

```bash
python -m venv venv-dashboard
./venv-dashboard/bin/pip install -r requirements-dashboard.txt
./venv-dashboard/bin/streamlit run dashboard/app.py
```

Puis `http://localhost:8501`. À chaque enregistrement d'un fichier, Streamlit
propose de recharger la page : le retour est immédiat, on travaille sans jamais
relancer la commande.

---

## Ce que tu n'as pas à faire

**Aucun calcul.** Les écarts-types, les corrélations, les classements et les
comparaisons annuelles sont déjà calculés dans BigQuery, par la couche dbt. Six
tables les portent. L'application ne fait que les afficher.

Si tu te retrouves à écrire une moyenne ou un écart-type en Python, arrête-toi :
la valeur existe déjà quelque part, et la recalculer donnerait un chiffre
différent de celui du rapport.

**Aucun SQL.** Tout passe par `donnees.py`. Une fonction par table, elle rend un
DataFrame pandas. Si tu as besoin d'une donnée qui n'y est pas, ajoute une
fonction là-bas plutôt qu'une requête dans une page.

---

## Où est quoi

| Fichier | Contenu |
|---|---|
| `app.py` | navigation et filtres. Tu n'as normalement pas à y toucher. |
| `donnees.py` | toutes les requêtes BigQuery, mises en cache |
| `style.py` | palette, mise en forme commune des graphiques, `nb()` |
| `questions/q1_regime.py` … `q5_tension.py` | **une page par fichier, c'est ici que tu travailles** |

Chaque page expose trois choses :

```python
TITRE = "…"          # le titre affiché
REPONSE = "…"        # la phrase qui donne la réponse, sous le titre
FILTRES = [...]      # quels filtres la page utilise (facultatif)

def rendre(filtres):
    ...              # les métriques et les graphiques
```

---

## Le modèle à suivre

`docs/maquette/tableau-de-bord.html` s'ouvre par double-clic. C'est la
**maquette de référence** : elle montre à quoi chaque page doit ressembler et,
surtout, **quels chiffres doivent apparaître**. Si ton graphique affiche autre
chose, c'est qu'une colonne n'est pas la bonne.

Elle a été construite avec les mêmes données. Elle ne bouge pas, l'application
si : les chiffres peuvent différer légèrement d'un jour à l'autre, le pipeline
tourne tous les jours ouvrés. C'est normal, c'est même le but.

---

## Ajouter ou modifier un graphique

Les graphiques sont faits avec Plotly. Le schéma est toujours le même :

```python
import plotly.graph_objects as go
import style as s

fig = go.Figure()
fig.add_bar(x=d["annee"], y=d["volatilite"], marker_color=s.BLEU)
st.plotly_chart(s.habiller(fig, hauteur=380), width="stretch")
```

`s.habiller()` applique le fond blanc, la grille en gris clair, la police et la
légende. **Appelle-la sur chaque figure** : c'est ce qui fait que les cinq pages
se ressemblent.

Les types utiles :

| Besoin | Appel |
|---|---|
| barres horizontales | `fig.add_bar(y=…, x=…, orientation="h")` |
| colonnes | `fig.add_bar(x=…, y=…)` |
| barres empilées | plusieurs `add_bar` + `fig.update_layout(barmode="stack")` |
| courbes | `fig.add_scatter(x=…, y=…, mode="lines+markers")` |
| nuage de points | `fig.add_scatter(x=…, y=…, mode="markers")` |

---

## Les règles de couleur, à ne pas contourner

La palette est dans `style.py` et elle a été vérifiée pour le daltonisme. Ne pas
l'élargir sans revalider.

**Une couleur suit une entité, jamais un rang.** Si un filtre retire une série,
les autres gardent leur teinte. Ne jamais colorer « le plus grand en foncé, le
plus petit en clair » quand les catégories n'ont pas d'ordre naturel : la
longueur de la barre dit déjà la valeur.

**Le rouge `s.ALERTE` est réservé aux périodes de tension.** Ne pas s'en servir
comme cinquième couleur de série, sinon il ne veut plus rien dire.

**Le vert et le jaune ont un contraste faible sur fond blanc.** Partout où ils
servent, afficher la valeur en étiquette à côté de la barre. C'est déjà fait
dans les pages existantes, garde ce réflexe.

**Pas de camembert** pour les exportations : les quatre catégories ne totalisent
pas 100 %.

**Jamais deux axes verticaux** sur un même graphique. Deux mesures d'échelles
différentes, ce sont deux graphiques.

---

## Se connecter à BigQuery

L'application utilise un compte de service **en lecture seule**, limité au
dataset `marts`. Il ne peut ni écrire, ni lire `raw`, ni lire `marts_staging`.
Vérifiable :

```bash
./venv-dashboard/bin/python dashboard/donnees.py
```

Cela affiche l'adresse du compte, une lecture qui passe et une qui est refusée.

La clé est cherchée dans cet ordre :

1. `st.secrets["gcp_service_account"]`, ce que lit Streamlit Community Cloud
2. la variable d'environnement `MBDA_DASHBOARD_KEYFILE`
3. `~/.gcp/mbda-dashboard-ro.json`, le chemin par défaut

**La clé n'est jamais dans le dépôt.** Le `.gitignore` bloque tous les `.json`
pour cette raison. Gabar te la transmettra directement.

---

## Mettre en ligne

Sur [share.streamlit.io](https://share.streamlit.io), connecter le dépôt,
pointer sur `dashboard/app.py`, et coller le contenu de la clé dans
*Settings* → *Secrets*, sous cette forme :

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

L'hébergement est gratuit et ne demande pas de carte bancaire.

---

## Si quelque chose bloque

**« Aucun identifiant trouvé ».** La clé n'est pas là où l'application la
cherche. Voir la section précédente.

**Les données paraissent vides ou anciennes.** Le cache dure dix minutes. Le
bouton *Rafraîchir les données* en bas du volet de gauche le vide.

**Un chiffre ne correspond pas à la maquette.** Vérifie la colonne : il y a
souvent `volatilite` et `volatilite_hors_anomalie` côte à côte, et elles ne
disent pas la même chose. La seconde écarte les deux séances du pétrole WTI à
prix négatif.

**Une erreur `403` sur `raw` ou `marts_staging`.** C'est voulu. Le compte ne
lit que `marts`. Si une donnée manque, elle doit être ajoutée à une table de
`marts` par la couche dbt, pas contournée ici.
