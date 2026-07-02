
    
    

select
    lineup_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."fact_player_match"
where lineup_sk is not null
group by lineup_sk
having count(*) > 1


