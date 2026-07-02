
    
    

select
    team_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."dim_team"
where team_sk is not null
group by team_sk
having count(*) > 1


