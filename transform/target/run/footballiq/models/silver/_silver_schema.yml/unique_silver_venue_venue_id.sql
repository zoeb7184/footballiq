
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    venue_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_venue"
where venue_id is not null
group by venue_id
having count(*) > 1



  
  
      
    ) dbt_internal_test