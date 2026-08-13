-- Indicateurs annuels par instrument.
-- Deux performances : en devise de cotation, c'est l'actif seul ; en euros,
-- le change est dedans. Ne pas citer l'une pour l'autre.
-- L'annee en cours est forcement incomplete, voir annee_complete.

with base as (
    select
        f.instrument_id,
        extract(year from f.date_cotation) as annee,
        f.date_cotation,
        f.cloture,
        f.cloture_eur,
        f.volume,
        f.variation_pct,
        f.variation_exploitable
    from {{ ref('fct_cotation_journaliere') }} as f
),

annuel as (
    select
        instrument_id,
        annee,
        count(*) as jours_cotes,
        min(date_cotation) as premier_jour,
        max(date_cotation) as dernier_jour,
        countif(not variation_exploitable and variation_pct is not null)
            as observations_ecartees,
        stddev(variation_pct) as volatilite,
        stddev(if(variation_exploitable, variation_pct, null))
            as volatilite_hors_anomalie,
        avg(abs(if(variation_exploitable, variation_pct, null)))
            as amplitude_moyenne,
        avg(volume) as volume_moyen,
        array_agg(cloture order by date_cotation asc limit 1)[offset(0)]
            as cloture_debut,
        array_agg(cloture order by date_cotation desc limit 1)[offset(0)]
            as cloture_fin,
        array_agg(cloture_eur order by date_cotation asc limit 1)[offset(0)]
            as cloture_eur_debut,
        array_agg(cloture_eur order by date_cotation desc limit 1)[offset(0)]
            as cloture_eur_fin
    from base
    group by instrument_id, annee
),

performance as (
    select
        *,
        round((cloture_fin / nullif(cloture_debut, 0) - 1) * 100, 4)
            as performance_pct,
        round((cloture_eur_fin / nullif(cloture_eur_debut, 0) - 1) * 100, 4)
            as performance_eur_pct
    from annuel
)

select
    p.instrument_id,
    i.libelle,
    i.classe_actif,
    i.secteur,
    i.categorie_export,
    p.annee,
    p.jours_cotes,
    p.jours_cotes >= 200 as annee_complete,
    p.premier_jour,
    p.dernier_jour,
    p.observations_ecartees,
    round(p.volatilite, 4) as volatilite,
    round(p.volatilite_hors_anomalie, 4) as volatilite_hors_anomalie,
    round(p.amplitude_moyenne, 4) as amplitude_moyenne,
    round(p.volume_moyen, 2) as volume_moyen,
    p.cloture_debut,
    p.cloture_fin,
    round(p.cloture_eur_debut, 4) as cloture_eur_debut,
    round(p.cloture_eur_fin, 4) as cloture_eur_fin,
    p.performance_pct,
    p.performance_eur_pct,
    round(
        p.performance_pct - lag(p.performance_pct) over (
            partition by p.instrument_id order by p.annee
        ), 4) as ecart_performance_annee_precedente
from performance as p
join {{ ref('dim_instrument') }} as i using (instrument_id)
