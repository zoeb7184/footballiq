select
    team_id::int                          as team_id,
    team_name                             as team_name,
    upper(fifa_code)                      as fifa_code,
    group_letter                          as group_letter,
    confederation                         as confederation,
    fifa_ranking_pre_tournament::int      as fifa_ranking,
    elo_rating::int                       as elo_rating,
    manager_name                          as manager_name
from {{ source('bronze', 'raw_teams') }}
where {{ latest_load('teams.csv') }}
