
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    referee_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_referee"
where referee_id is not null
group by referee_id
having count(*) > 1



  
  
      
    ) dbt_internal_test