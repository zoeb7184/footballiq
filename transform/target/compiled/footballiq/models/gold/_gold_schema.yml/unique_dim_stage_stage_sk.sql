
    
    

select
    stage_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."dim_stage"
where stage_sk is not null
group by stage_sk
having count(*) > 1


