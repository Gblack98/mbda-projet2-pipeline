with variabilite as (
    select
        devise_cible,
        stddev(taux) / nullif(avg(taux), 0) as coefficient_variation
    from {{ ref('stg_taux_change') }}
    group by devise_cible
)

select
    d.devise_id,
    d.libelle as nom_devise,
    d.symbole,
    v.coefficient_variation,
    case
        when d.devise_id = 'EUR' then 'reference'
        when v.coefficient_variation < 0.005 then 'arrime'
        when v.coefficient_variation < 0.10 then 'gere'
        else 'flottant'
    end as regime
from {{ ref('stg_devises') }} d
left join variabilite v
    on d.devise_id = v.devise_cible
