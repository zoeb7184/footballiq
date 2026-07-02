
    
    

with child as (
    select player_sk as from_field
    from "footballiq"."gold"."fact_match_event"
    where player_sk is not null
),

parent as (
    select player_sk as to_field
    from "footballiq"."gold"."dim_player"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


