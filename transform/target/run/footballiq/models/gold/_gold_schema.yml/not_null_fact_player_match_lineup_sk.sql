
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select lineup_sk
from "footballiq"."gold"."fact_player_match"
where lineup_sk is null



  
  
      
    ) dbt_internal_test