
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select fifa_code
from "footballiq"."silver"."silver_team"
where fifa_code is null



  
  
      
    ) dbt_internal_test