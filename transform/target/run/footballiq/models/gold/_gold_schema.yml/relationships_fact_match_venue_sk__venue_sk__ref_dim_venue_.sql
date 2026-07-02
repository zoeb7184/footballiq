
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select venue_sk as from_field
    from "footballiq"."gold"."fact_match"
    where venue_sk is not null
),

parent as (
    select venue_sk as to_field
    from "footballiq"."gold"."dim_venue"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test