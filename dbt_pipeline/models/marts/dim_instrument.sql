select
    i.instrument_id,
    i.libelle,
    i.classe_actif,
    i.secteur,
    i.sous_secteur,
    s.categorie_export
from {{ ref('stg_instruments') }} as i
left join {{ ref('stg_secteurs') }} as s
    on i.secteur = s.secteur
