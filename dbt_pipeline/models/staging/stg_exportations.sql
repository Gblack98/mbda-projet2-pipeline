select
    pays,
    annee,
    categorie,
    part_exportations,
    recupere_le
from {{ source('raw', 'exportations') }}
