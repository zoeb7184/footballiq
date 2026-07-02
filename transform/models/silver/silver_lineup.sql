-- Grain: player registered to a match (incl. unused subs with 0 minutes).
select
    lineup_id::int            as lineup_id,
    match_id::int             as match_id,
    player_id::int            as player_id,
    team_id::int              as team_id,
    is_starting_xi = '1'      as is_starting_xi,
    tactical_position         as tactical_position,
    minutes_played::int       as minutes_played
from {{ source('bronze', 'raw_match_lineups') }}
where {{ latest_load('match_lineups.csv') }}
