select
    devise_id,
    libelle as nom_devise,
    symbole
from {{ ref('stg_devises') }}
