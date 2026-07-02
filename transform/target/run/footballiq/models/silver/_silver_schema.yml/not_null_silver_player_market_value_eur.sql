
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select market_value_eur
from "footballiq"."silver"."silver_player"
where market_value_eur is null



  
  
      
    ) dbt_internal_test