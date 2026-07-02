
    
    

select
    referee_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."dim_referee"
where referee_sk is not null
group by referee_sk
having count(*) > 1


