select
    referee_id::int                      as referee_id,
    name                                 as referee_name,
    country                              as country,
    avg_cards_per_game::numeric(4, 2)    as avg_cards_per_game
from "footballiq"."bronze"."raw_referees"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'referees.csv'
        order by ingested_at desc
        limit 1
    )
