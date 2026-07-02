
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    event_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."fact_match_event"
where event_sk is not null
group by event_sk
having count(*) > 1



  
  
      
    ) dbt_internal_test