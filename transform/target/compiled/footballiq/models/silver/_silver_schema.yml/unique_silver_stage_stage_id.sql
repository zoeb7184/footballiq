
    
    

select
    stage_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_stage"
where stage_id is not null
group by stage_id
having count(*) > 1


