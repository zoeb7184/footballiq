-- Typed match rows from the latest load, BEFORE contract filtering.
-- Ephemeral: exists only as the shared input of silver_match / quarantine_match.


select
    match_id::int                              as match_id,
    "date"::date                               as match_date,
    kickoff_time_utc::time                     as kickoff_utc,
    stage_id::int                              as stage_id,
    venue_id::int                              as venue_id,
    home_team_id::int                          as home_team_id,
    nullif(away_team_id, '')::int              as away_team_id,
    nullif(home_score, '')::int                as home_score,
    nullif(away_score, '')::int                as away_score,
    status                                     as status,
    nullif(home_xg, '')::numeric(5, 2)         as home_xg,
    nullif(away_xg, '')::numeric(5, 2)         as away_xg,
    nullif(referee_id, '')::int                as referee_id,
    nullif(player_of_the_match_id, '')::int    as player_of_the_match_id
from "footballiq"."bronze"."raw_matches"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'matches.csv'
        order by ingested_at desc
        limit 1
    )
