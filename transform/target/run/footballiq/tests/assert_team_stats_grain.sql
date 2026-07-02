
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Grain contract: every match covered by team stats has exactly 2 rows.
select match_id, count(*) as rows_for_match
from "footballiq"."gold"."fact_match_team_stats"
group by match_id
having count(*) != 2
  
  
      
    ) dbt_internal_test