
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select venue_sk
from "footballiq"."gold"."dim_venue"
where venue_sk is null



  
  
      
    ) dbt_internal_test