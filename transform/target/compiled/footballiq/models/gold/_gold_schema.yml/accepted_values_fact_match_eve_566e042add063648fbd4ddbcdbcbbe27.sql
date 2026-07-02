
    
    

with all_values as (

    select
        event_type as value_field,
        count(*) as n_records

    from "footballiq"."gold"."fact_match_event"
    group by event_type

)

select *
from all_values
where value_field not in (
    'Goal','Assist','Yellow Card','Red Card','VAR Review'
)


