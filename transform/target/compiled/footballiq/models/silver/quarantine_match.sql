with __dbt__cte__silver_match_base as (
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

) -- Contract violations, preserved with a reason — never silently dropped
-- (physical architecture §1). Expected row count: 0.
select
    *,
    case
        when status not in ('Scheduled', 'Completed')
            then 'unknown status: ' || status
        when status = 'Completed' and (home_score is null or away_score is null)
            then 'completed match missing scores'
        when status = 'Completed' and (home_score < 0 or away_score < 0)
            then 'negative score'
        when status = 'Completed' and (home_xg is null or away_xg is null)
            then 'completed match missing xG'
        else 'unclassified violation'
    end as quarantine_reason
from __dbt__cte__silver_match_base
where not (
    (
        status = 'Scheduled'
    )
    or (
        status = 'Completed'
        and home_score is not null and away_score is not null
        and home_score >= 0 and away_score >= 0
        and home_xg is not null and away_xg is not null
    )
)