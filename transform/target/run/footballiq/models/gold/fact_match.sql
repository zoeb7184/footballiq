
  
    

  create  table "footballiq"."gold"."fact_match__dbt_tmp"
  
  
    as
  
  (
    -- Grain: one match. The ONLY place source nulls become reserved members
-- (physical architecture §2): null away team in knockout -> TBD (-2),
-- otherwise Unknown (-1).
select
    m.match_id,
    to_char(m.match_date, 'YYYYMMDD')::int                 as date_key,
    m.kickoff_utc,
    m.stage_id                                             as stage_sk,
    m.venue_id                                             as venue_sk,
    coalesce(m.referee_id, -1)                             as referee_sk,
    m.home_team_id                                         as home_team_sk,
    coalesce(
        m.away_team_id,
        case when s.is_knockout then -2 else -1 end
    )                                                      as away_team_sk,
    coalesce(m.player_of_the_match_id, -1)                 as player_of_match_sk,
    m.status,
    m.home_score,
    m.away_score,
    m.home_xg,
    m.away_xg
from "footballiq"."silver"."silver_match" as m
inner join "footballiq"."silver"."silver_stage" as s on m.stage_id = s.stage_id
  );
  