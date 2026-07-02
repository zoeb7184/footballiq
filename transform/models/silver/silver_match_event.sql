select
    event_id::int    as event_id,
    match_id::int    as match_id,
    minute::int      as minute,
    event_type       as event_type,
    team_id::int     as team_id,
    player_id::int   as player_id
from {{ source('bronze', 'raw_match_events') }}
where {{ latest_load('match_events.csv') }}
