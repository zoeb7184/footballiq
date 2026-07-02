
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

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



  
  
      
    ) dbt_internal_test