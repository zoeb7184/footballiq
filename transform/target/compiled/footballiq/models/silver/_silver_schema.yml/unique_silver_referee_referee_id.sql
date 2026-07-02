
    
    

select
    referee_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_referee"
where referee_id is not null
group by referee_id
having count(*) > 1


