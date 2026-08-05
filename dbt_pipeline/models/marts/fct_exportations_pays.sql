{{ config(cluster_by=['pays', 'annee']) }}

select
    pays,
    annee,
    categorie as categorie_export,
    part_exportations
from {{ ref('stg_exportations') }}
where part_exportations is not null
