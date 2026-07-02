
    
    

with child as (
    select referee_sk as from_field
    from "footballiq"."gold"."fact_match"
    where referee_sk is not null
),

parent as (
    select referee_sk as to_field
    from "footballiq"."gold"."dim_referee"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


