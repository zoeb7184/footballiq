
    
    

with all_values as (

    select
        position as value_field,
        count(*) as n_records

    from "footballiq"."silver"."silver_player"
    group by position

)

select *
from all_values
where value_field not in (
    'GK','DEF','MID','FWD'
)


