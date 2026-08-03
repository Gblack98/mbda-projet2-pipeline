select
    date_cotation,
    instrument_id,
    ouverture,
    plus_haut,
    plus_bas,
    cloture,
    volume,
    devise_cotation,
    recupere_le
from {{ source('raw', 'cotations') }}
