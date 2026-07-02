
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select referee_id
from "footballiq"."silver"."silver_referee"
where referee_id is null



  
  
      
    ) dbt_internal_test