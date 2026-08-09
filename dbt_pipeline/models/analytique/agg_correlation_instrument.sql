-- Question 4 : les societes extractives suivent-elles leur matiere premiere.
--
-- Correlation de Pearson entre les variations quotidiennes de l'action et
-- celles de sa matiere, sur les seules seances ou les deux ont cote. La paire
-- temoin Orange / Or est ce qui valide la methode : Orange n'a aucun lien avec
-- l'or, sa correlation doit rester proche de zero. Si elle monte, c'est le
-- calcul qui est en cause, pas le marche.

with variations as (
    select date_cotation, instrument_id, variation_pct
    from {{ ref('fct_cotation_journaliere') }}
    where variation_exploitable
),

apparie as (
    select
        p.paire_id,
        p.libelle,
        p.temoin,
        p.instrument_action,
        p.instrument_matiere,
        a.date_cotation,
        a.variation_pct as variation_action,
        m.variation_pct as variation_matiere
    from {{ ref('paires_instrument') }} as p
    join variations as a on a.instrument_id = p.instrument_action
    join variations as m on m.instrument_id = p.instrument_matiere
        and m.date_cotation = a.date_cotation
)

select
    paire_id,
    libelle,
    instrument_action,
    instrument_matiere,
    temoin,
    count(*) as jours_communs,
    min(date_cotation) as debut,
    max(date_cotation) as fin,
    round(corr(variation_action, variation_matiere), 4) as correlation,
    round(pow(corr(variation_action, variation_matiere), 2), 4)
        as part_variance_expliquee,
    round(stddev(variation_action), 4) as volatilite_action,
    round(stddev(variation_matiere), 4) as volatilite_matiere
from apparie
group by paire_id, libelle, instrument_action, instrument_matiere, temoin
