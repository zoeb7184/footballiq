
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select stage_sk
from "footballiq"."gold"."dim_stage"
where stage_sk is null



  
  
      
    ) dbt_internal_test