
    
    

select
    fifa_code as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_team"
where fifa_code is not null
group by fifa_code
having count(*) > 1


