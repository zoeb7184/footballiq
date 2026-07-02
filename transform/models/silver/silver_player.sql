-- Player registry. market_value_eur fully populated (profile batch 2);
-- club_team trimmed as the normalization baseline for the talent-flow graph.
select
    player_id::int             as player_id,
    team_id::int               as team_id,
    player_name                as player_name,
    position                   as position,
    trim(club_team)            as club_team,
    market_value_eur::bigint   as market_value_eur,
    caps::int                  as caps,
    date_of_birth::date        as date_of_birth,
    height_cm::int             as height_cm,
    goals::int                 as international_goals
from {{ source('bronze', 'raw_squads_and_players') }}
where {{ latest_load('squads_and_players.csv') }}
