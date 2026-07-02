
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select event_sk
from "footballiq"."gold"."fact_match_event"
where event_sk is null



  
  
      
    ) dbt_internal_test