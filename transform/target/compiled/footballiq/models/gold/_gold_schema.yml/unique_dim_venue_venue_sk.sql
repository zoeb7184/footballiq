
    
    

select
    venue_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."dim_venue"
where venue_sk is not null
group by venue_sk
having count(*) > 1


