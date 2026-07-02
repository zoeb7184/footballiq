
  
    

  create  table "footballiq"."silver"."silver_team_match_stats__dbt_tmp"
  
  
    as
  
  (
    -- Partial-coverage source (66/76 completed matches at profiling) — declared,
-- not assumed complete. player_of_the_match name column intentionally
-- excluded: reconciliation-only (physical architecture §3).
select
    match_id::int                                   as match_id,
    team_id::int                                    as team_id,
    possession_pct::int                             as possession_pct,
    total_shots::int                                as total_shots,
    shots_on_target::int                            as shots_on_target,
    corners::int                                    as corners,
    fouls::int                                      as fouls,
    offsides::int                                   as offsides,
    saves::int                                      as saves,
    coalesce(nullif(data_source, ''), 'unverified') as data_source,
    last_updated::date                              as last_updated
from "footballiq"."bronze"."raw_match_team_stats"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'match_team_stats.csv'
        order by ingested_at desc
        limit 1
    )

  );
  