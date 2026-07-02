
    
    

select
    venue_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_venue"
where venue_id is not null
group by venue_id
having count(*) > 1


