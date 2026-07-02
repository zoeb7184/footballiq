
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    player_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."player_tournament_snapshot"
where player_sk is not null
group by player_sk
having count(*) > 1



  
  
      
    ) dbt_internal_test