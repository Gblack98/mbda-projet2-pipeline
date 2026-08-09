-- Question 5 : quelles ont ete les periodes de tension.
--
-- Un mois est dit sous tension quand la dispersion des variations quotidiennes,
-- tous instruments confondus, depasse trois fois la mediane des mois observes.
-- Le seuil est relatif a l'historique du jeu, pas fixe a la main : il suit les
-- donnees quand elles s'allongent.

with mensuel as (
    select
        date_trunc(date_cotation, month) as mois,
        count(*) as observations,
        countif(not variation_exploitable) as observations_ecartees,
        count(distinct instrument_id) as instruments,
        stddev(variation_pct) as volatilite,
        stddev(if(variation_exploitable, variation_pct, null))
            as volatilite_hors_anomalie
    from {{ ref('fct_cotation_journaliere') }}
    where variation_pct is not null
    group by mois
),

reference as (
    select percentile_cont(volatilite, 0.5) over () as mediane
    from mensuel
    limit 1
)

select
    m.mois,
    extract(year from m.mois) as annee,
    m.instruments,
    m.observations,
    m.observations_ecartees,
    round(m.volatilite, 4) as volatilite,
    round(m.volatilite_hors_anomalie, 4) as volatilite_hors_anomalie,
    round(r.mediane, 4) as mediane_historique,
    round(m.volatilite / nullif(r.mediane, 0), 2) as multiple_mediane,
    m.volatilite > 3 * r.mediane as est_tension,
    round(m.volatilite - lag(m.volatilite) over (order by m.mois), 4)
        as ecart_mois_precedent
from mensuel as m
cross join reference as r
