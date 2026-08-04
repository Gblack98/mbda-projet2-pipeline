select
    pays,
    categorie,
    annee as derniere_annee_disponible,
    part_exportations as poids_export
from {{ ref('stg_exportations') }}
where part_exportations is not null
qualify row_number() over (
    partition by pays, categorie
    order by annee desc
) = 1
