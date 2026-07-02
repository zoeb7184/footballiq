
  
    

  create  table "footballiq"."silver"."silver_stage__dbt_tmp"
  
  
    as
  
  (
    select
    stage_id::int                        as stage_id,
    stage_name                           as stage_name,
    lower(is_knockout) in ('true', '1')  as is_knockout
from "footballiq"."bronze"."raw_tournament_stages"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'tournament_stages.csv'
        order by ingested_at desc
        limit 1
    )

  );
  