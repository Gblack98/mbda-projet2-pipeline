# Questions métier

Cinq questions auxquelles le tableau de bord doit répondre. Chacune est
calculable avec les tables de `marts`.

## 1. Le régime de change protège-t-il de la volatilité ?

Comparer la variabilité des monnaies selon leur régime. Le XOF est arrimé à
l'euro depuis 1999, l'ouguiya et le naira flottent.

`dim_devise.regime` · `dim_devise.coefficient_variation`

Mesure sur dix ans : les monnaies arrimées affichent un coefficient nul, les
flottantes 0,32 en moyenne.

## 2. Quelle classe d'actif est la plus volatile, et comment évolue-t-elle ?

Écart-type des variations quotidiennes par classe et par période.

`fct_cotation_journaliere.variation_pct` · `dim_instrument.classe_actif` ·
`dim_temps.annee` / `trimestre`

Attention : la volatilité se mesure sur les **variations**, pas sur les prix.
Calculer l'écart-type de `cloture_eur` par classe mélangerait des instruments
cotés à 2 € et à 800 € — le résultat mesurerait l'écart entre eux, pas leur
agitation.

## 3. Quel pays a le panier d'exportation le plus exposé ?

Croiser la part de chaque catégorie dans les exportations d'un pays avec la
volatilité des instruments de cette catégorie.

`fct_exportations_pays` · `dim_instrument.categorie_export` ·
`fct_cotation_journaliere`

La jointure passe par `categorie_export`, présent des deux côtés. Les deux
tables de faits ne se joignent jamais directement : leurs grains diffèrent
(pays × catégorie × année contre instrument × jour).

## 4. Les sociétés extractives suivent-elles le cours de leur matière ?

Comparer les variations d'une action et de la matière première correspondante :
Kinross et l'or, Kosmos et le gaz, Woodside et le Brent.

`fct_cotation_journaliere.variation_pct` · `dim_instrument.secteur`

## 5. Quelles ont été les périodes de tension sur dix ans ?

Repérer les périodes où la volatilité dépasse sa moyenne, et voir quels
instruments ont bougé ensemble.

`fct_cotation_journaliere.variation_pct` · `dim_temps`

## Ce que le tableau de bord doit couvrir

Une page par question. Les tables à utiliser sont dans le dataset `marts` ;
`marts_staging` ne sert qu'à dbt et n'a pas à être exposé.
