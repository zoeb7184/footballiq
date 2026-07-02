
  
    

  create  table "footballiq"."gold"."dim_team__dbt_tmp"
  
  
    as
  
  (
    -- Surrogate = natural key at MVP (single source, deterministic); reserved
-- members -1 Unknown / -2 TBD seeded here (logical model §2).
select
    team_id            as team_sk,
    team_id            as team_id_nat,
    team_name,
    fifa_code,
    group_letter,
    confederation,
    fifa_ranking,
    elo_rating,
    manager_name
from "footballiq"."silver"."silver_team"

union all
select -1, null, 'Unknown', 'UNK', null, null, null, null, null

union all
select -2, null, 'To Be Determined', 'TBD', null, null, null, null, null
  );
  