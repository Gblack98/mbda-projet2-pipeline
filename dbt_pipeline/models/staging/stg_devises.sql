select
    devise_id,
    libelle,
    symbole,
    publiee_depuis,
    publiee_jusqua
from {{ source('raw', 'devises') }}
