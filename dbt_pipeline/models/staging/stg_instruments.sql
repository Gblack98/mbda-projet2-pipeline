select
    instrument_id,
    libelle,
    classe_actif,
    secteur,
    sous_secteur
from {{ source('raw', 'instruments') }}
