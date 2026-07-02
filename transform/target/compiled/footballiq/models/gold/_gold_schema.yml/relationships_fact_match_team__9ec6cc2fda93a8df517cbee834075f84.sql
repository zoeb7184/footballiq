
    
    

with child as (
    select team_sk as from_field
    from "footballiq"."gold"."fact_match_team_stats"
    where team_sk is not null
),

parent as (
    select team_sk as to_field
    from "footballiq"."gold"."dim_team"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


