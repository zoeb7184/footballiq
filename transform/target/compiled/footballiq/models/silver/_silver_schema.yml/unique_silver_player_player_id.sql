
    
    

select
    player_id as unique_field,
    count(*) as n_records

from "footballiq"."silver"."silver_player"
where player_id is not null
group by player_id
having count(*) > 1


