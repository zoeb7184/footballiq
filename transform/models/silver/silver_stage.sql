select
    stage_id::int                        as stage_id,
    stage_name                           as stage_name,
    lower(is_knockout) in ('true', '1')  as is_knockout
from {{ source('bronze', 'raw_tournament_stages') }}
where {{ latest_load('tournament_stages.csv') }}
