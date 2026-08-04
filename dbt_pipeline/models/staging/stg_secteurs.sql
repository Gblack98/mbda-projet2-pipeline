select
    secteur,
    categorie_export
from {{ source('raw', 'secteurs') }}
