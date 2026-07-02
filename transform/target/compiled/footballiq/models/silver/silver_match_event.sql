select
    event_id::int    as event_id,
    match_id::int    as match_id,
    minute::int      as minute,
    event_type       as event_type,
    team_id::int     as team_id,
    player_id::int   as player_id
from "footballiq"."bronze"."raw_match_events"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'match_events.csv'
        order by ingested_at desc
        limit 1
    )
