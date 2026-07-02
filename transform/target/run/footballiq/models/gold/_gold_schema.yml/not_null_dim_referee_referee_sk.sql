
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select referee_sk
from "footballiq"."gold"."dim_referee"
where referee_sk is null



  
  
      
    ) dbt_internal_test