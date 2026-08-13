{{ config(cluster_by=['instrument_id', 'date_cotation']) }}

with taux_eur as (
    select date_taux, devise_cible, taux
    from {{ ref('stg_taux_change') }}
    where devise_base = 'EUR'
),

bornes as (
    {{ bornes_cotation() }}
),
calendrier as (
    select jour, devise_cible
    from bornes,
         unnest(generate_date_array(bornes.debut, bornes.fin)) as jour
    cross join (select distinct devise_cible from taux_eur)
),
taux_complet as (
    select
        c.jour as date_taux,
        c.devise_cible,
        coalesce(
            last_value(t.taux ignore nulls) over (
                partition by c.devise_cible order by c.jour
                rows between unbounded preceding and current row
            ),
            first_value(t.taux ignore nulls) over (
                partition by c.devise_cible order by c.jour
                rows between current row and unbounded following
            )
        ) as taux
    from calendrier as c
    left join taux_eur as t
        on t.date_taux = c.jour
        and t.devise_cible = c.devise_cible
),
cotations_mappees as (
    select c.*, m.devise_pivot, m.facteur
    from {{ ref('stg_cotations') }} as c
    left join {{ ref('mapping_devise_cotation') }} as m
        on c.devise_cotation = m.devise_cotation
),

with_variation as (
select
    c.date_cotation,
    c.instrument_id,
    c.devise_cotation,
    c.devise_pivot,
    c.ouverture,
    c.plus_haut,
    c.plus_bas,
    c.cloture,
    c.volume,
    case
        when c.devise_pivot = 'EUR' then c.cloture / c.facteur
        else (c.cloture / c.facteur) / t.taux
    end as cloture_eur,
    c.recupere_le
from cotations_mappees as c
left join taux_complet as t
    on t.date_taux = c.date_cotation
    and t.devise_cible = c.devise_pivot
),

precedente as (
select
    *,
    lag(cloture) over (
        partition by instrument_id order by date_cotation
    ) as cloture_precedente
from with_variation
)

select
    * except (cloture_precedente),
    round((cloture / nullif(cloture_precedente, 0) - 1) * 100, 4) as variation_pct,
    -- Le WTI a cote -37,63 le 2020-04-20. Entre clotures de signes opposes,
    -- le pourcentage ne veut rien dire (-305 % puis -126 %). Les lignes
    -- restent, ce drapeau sert a les ecarter d'une moyenne.
    coalesce(cloture > 0 and cloture_precedente > 0, false) as variation_exploitable
from precedente
