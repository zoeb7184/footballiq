
  
    

  create  table "footballiq"."gold"."dim_date__dbt_tmp"
  
  
    as
  
  (
    -- Calendar spanning the tournament (generated, standard practice).
with bounds as (
    select
        min(match_date) as start_date,
        max(match_date) as end_date
    from "footballiq"."silver"."silver_match"
)

select
    to_char(d, 'YYYYMMDD')::int            as date_key,
    d::date                                as calendar_date,
    extract(year from d)::int              as year,
    extract(month from d)::int             as month,
    extract(day from d)::int               as day,
    to_char(d, 'Dy')                       as day_name,
    extract(isodow from d)::int in (6, 7)  as is_weekend
from bounds,
    generate_series(bounds.start_date, bounds.end_date, interval '1 day') as d
  );
  