-- Question 2, annee par annee.
-- Sur variation_pct, jamais sur cloture_eur : sinon on compare un titre a
-- 2 EUR et un autre a 800 EUR. stddev, donc ecart-type d'echantillon.

with base as (
    select
        i.classe_actif,
        t.annee,
        f.instrument_id,
        f.variation_pct,
        f.variation_exploitable
    from {{ ref('fct_cotation_journaliere') }} as f
    join {{ ref('dim_instrument') }} as i using (instrument_id)
    join {{ ref('dim_temps') }} as t on t.date_jour = f.date_cotation
    where f.variation_pct is not null
)

select
    classe_actif,
    annee,
    count(distinct instrument_id) as instruments,
    count(*) as observations,
    countif(not variation_exploitable) as observations_ecartees,
    round(stddev(variation_pct), 4) as volatilite,
    round(stddev(if(variation_exploitable, variation_pct, null)), 4)
        as volatilite_hors_anomalie,
    round(avg(abs(variation_pct)), 4) as amplitude_moyenne,
    round(avg(variation_pct), 4) as variation_moyenne,
    round(max(variation_pct), 4) as hausse_maximale,
    round(min(variation_pct), 4) as baisse_maximale
from base
group by classe_actif, annee
