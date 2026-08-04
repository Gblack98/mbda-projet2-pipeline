select
    date_jour,
    extract(year from date_jour) as annee,
    extract(quarter from date_jour) as trimestre,
    extract(month from date_jour) as mois,
    extract(day from date_jour) as jour,
    format_date('%A', date_jour) as jour_semaine,
    extract(dayofweek from date_jour) in (1, 7) as est_weekend
from unnest(generate_date_array('2016-01-01', current_date())) as date_jour
