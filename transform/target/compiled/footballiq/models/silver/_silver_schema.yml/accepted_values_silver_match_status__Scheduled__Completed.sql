
    
    

with all_values as (

    select
        status as value_field,
        count(*) as n_records

    from "footballiq"."silver"."silver_match"
    group by status

)

select *
from all_values
where value_field not in (
    'Scheduled','Completed'
)


