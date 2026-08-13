-- Orange n'a aucun lien avec l'or. Si cette correlation monte, c'est le
-- calcul qui derape, et les 0,6 des minieres ne valent plus rien.
-- Seuil large a 0,15 : le bruit de 2 500 seances ne doit pas le declencher.

select
    paire_id,
    libelle,
    correlation
from {{ ref('agg_correlation_instrument') }}
where temoin
  and abs(correlation) >= 0.15
