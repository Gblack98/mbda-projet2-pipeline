-- La paire temoin ne mesure rien de reel : Orange n'a aucun lien avec l'or.
-- Sa correlation doit donc rester proche de zero. Si elle monte, ce n'est pas
-- le marche qui a change, c'est le calcul de correlation qui est fausse, et
-- les 0,6 des minieres ne veulent alors plus rien dire.
--
-- Le seuil de 0,15 est large a dessein : il laisse passer le bruit d'un
-- echantillon de 2 500 seances et n'attrape qu'une vraie derive.

select
    paire_id,
    libelle,
    correlation
from {{ ref('agg_correlation_instrument') }}
where temoin
  and abs(correlation) >= 0.15
