-- Indicateurs annuels par instrument : la table de synthese sur laquelle
-- s'appuient les comparaisons d'une annee sur l'autre.
--
-- Deux performances sont calculees. Celle en devise de cotation isole le
-- comportement de l'actif. Celle en euros y ajoute l'effet de change, c'est
-- le rendement qu'aurait vu un investisseur de la zone euro. Les citer l'une
-- pour l'autre est l'erreur classique, d'ou les deux colonnes distinctes.
--
-- L'annee en cours est incomplete par construction : jours_cotes le dit, et
-- annee_complete permet de l'ecarter d'une comparaison.

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
