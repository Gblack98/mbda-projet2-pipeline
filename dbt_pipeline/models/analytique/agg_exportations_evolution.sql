-- Question 3 : quel pays a le panier d'exportation le plus expose, et comment
-- cette exposition bouge dans le temps.
--
-- part_exportations est deja une part en pourcentage : les ecarts d'une annee
-- sur l'autre se lisent donc en points, pas en pourcentage de pourcentage.
-- Les deux sont fournis, l'ecart en points est celui a citer.
--
-- Les annees ne se suivent pas toujours : la Banque Mondiale laisse des trous
-- selon les pays. lag() porte sur l'annee precedente presente dans les donnees,
-- d'ou la colonne annee_precedente qui dit sur quoi la comparaison porte.

with classe as (
    select
        pays,
        annee,
        categorie_export,
        part_exportations,
        row_number() over (
            partition by pays, annee order by part_exportations desc
        ) as rang_categorie,
        sum(part_exportations) over (partition by pays, annee)
            as part_couverte_annee
    from {{ ref('fct_exportations_pays') }}
),

evolution as (
    select
        *,
        lag(part_exportations) over (
            partition by pays, categorie_export order by annee
        ) as part_annee_precedente,
        lag(annee) over (
            partition by pays, categorie_export order by annee
        ) as annee_precedente
    from classe
)

select
    pays,
    annee,
    categorie_export,
    part_exportations,
    rang_categorie,
    rang_categorie = 1 as est_categorie_dominante,
    round(part_couverte_annee, 4) as part_couverte_annee,
    annee_precedente,
    part_annee_precedente,
    round(part_exportations - part_annee_precedente, 4) as ecart_points,
    round(
        (part_exportations / nullif(part_annee_precedente, 0) - 1) * 100
    , 4) as evolution_pct
from evolution
