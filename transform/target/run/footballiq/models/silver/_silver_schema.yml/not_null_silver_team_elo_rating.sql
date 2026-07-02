
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select elo_rating
from "footballiq"."silver"."silver_team"
where elo_rating is null



  
  
      
    ) dbt_internal_test