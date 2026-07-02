
  
    

  create  table "footballiq"."silver"."silver_player_tournament_stats__dbt_tmp"
  
  
    as
  
  (
    -- Source-precomputed player-tournament aggregate. Dead columns (shots,
-- shots_on_target, average_rating — 100% null at profiling) are NOT promoted
-- from bronze. GK-only fields are structurally null for outfielders.
-- BI-only downstream: never an ML feature source (ML design §2B).
select
    player_id::int                                  as player_id,
    team_id::int                                    as team_id,
    matches_played::int                             as matches_played,
    matches_started::int                            as matches_started,
    minutes_played::int                             as minutes_played,
    goals::int                                      as goals,
    assists::int                                    as assists,
    yellow_cards::int                               as yellow_cards,
    red_cards::int                                  as red_cards,
    penalty_goals::int                              as penalty_goals,
    own_goals::int                                  as own_goals,
    nullif(clean_sheets, '')::int                   as clean_sheets,
    nullif(saves, '')::int                          as saves,
    nullif(goals_conceded, '')::int                 as goals_conceded,
    coalesce(nullif(data_source, ''), 'unverified') as data_source,
    nullif(last_verified, '')::date                 as last_verified
from "footballiq"."bronze"."raw_player_stats"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'player_stats.csv'
        order by ingested_at desc
        limit 1
    )

  );
  