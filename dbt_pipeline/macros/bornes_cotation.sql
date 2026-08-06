{% macro bornes_cotation() %}
select min(date_cotation) as debut, max(date_cotation) as fin
from {{ ref('stg_cotations') }}
{% endmacro %}
