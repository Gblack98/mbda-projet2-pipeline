-- Meme mesure que agg_correlation_instrument, decoupee par annee.
--
-- Une correlation calculee sur dix ans ecrase les ruptures. Le decoupage sert
-- de controle : une paire solide garde un coefficient stable d'une annee sur
-- l'autre. Une paire qui derive signale soit un changement reel de l'activite
-- de la societe, soit un probleme de serie. C'est ce decoupage qui a montre
-- que la paire barrick_or reste sous 0,25 pendant six ans la ou les autres
-- minieres aurifieres tiennent 0,5 a 0,7 : voir docs/questions-metier.md.

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
        extract(year from a.date_cotation) as annee,
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
    temoin,
    annee,
    count(*) as jours_communs,
    round(corr(variation_action, variation_matiere), 4) as correlation,
    round(
        corr(variation_action, variation_matiere)
        - lag(corr(variation_action, variation_matiere)) over (
            partition by paire_id order by annee
        ), 4) as ecart_annee_precedente
from apparie
group by paire_id, libelle, temoin, annee
