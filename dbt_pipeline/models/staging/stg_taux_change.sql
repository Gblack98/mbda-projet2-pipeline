select
    date_taux,
    devise_base,
    devise_cible,
    taux,
    recupere_le
from {{ source('raw', 'taux_change') }}
