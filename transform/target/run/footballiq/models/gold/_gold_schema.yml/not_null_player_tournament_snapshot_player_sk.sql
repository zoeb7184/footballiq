
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select player_sk
from "footballiq"."gold"."player_tournament_snapshot"
where player_sk is null



  
  
      
    ) dbt_internal_test