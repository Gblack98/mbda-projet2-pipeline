with taux_eur as (
    select date_taux, devise_cible, taux
    from {{ ref('stg_taux_change') }}
    where devise_base = 'EUR'
),

bornes as (
    select min(date_cotation) as debut, max(date_cotation) as fin
    from {{ ref('stg_cotations') }}
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
mapping as (
    select * from unnest([
        struct('USD' as devise_cotation, 'USD' as devise_pivot, 1 as facteur),
        struct('USX', 'USD', 100),
        struct('EUR', 'EUR', 1),
        struct('GBp', 'GBP', 100),
        struct('GBP', 'GBP', 1),
        struct('ZAc', 'ZAR', 100),
        struct('CAD', 'CAD', 1),
        struct('JPY', 'JPY', 1)
    ])
),

cotations_mappees as (
    select c.*, m.devise_pivot, m.facteur
    from {{ ref('stg_cotations') }} as c
    left join mapping as m
        on c.devise_cotation = m.devise_cotation
)
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
