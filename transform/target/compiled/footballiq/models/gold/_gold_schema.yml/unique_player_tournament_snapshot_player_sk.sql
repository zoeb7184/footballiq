
    
    

select
    player_sk as unique_field,
    count(*) as n_records

from "footballiq"."gold"."player_tournament_snapshot"
where player_sk is not null
group by player_sk
having count(*) > 1


