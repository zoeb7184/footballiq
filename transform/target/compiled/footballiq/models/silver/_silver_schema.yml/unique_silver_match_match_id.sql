
    
    

select
    match_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_match"
where match_id is not null
group by match_id
having count(*) > 1


