select
    team_id::int                          as team_id,
    team_name                             as team_name,
    upper(fifa_code)                      as fifa_code,
    group_letter                          as group_letter,
    confederation                         as confederation,
    fifa_ranking_pre_tournament::int      as fifa_ranking,
    elo_rating::int                       as elo_rating,
    manager_name                          as manager_name
from "footballiq"."bronze"."raw_teams"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'teams.csv'
        order by ingested_at desc
        limit 1
    )
