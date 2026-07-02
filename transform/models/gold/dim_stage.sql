select
    stage_id     as stage_sk,
    stage_id     as stage_id_nat,
    stage_name,
    is_knockout
from {{ ref('silver_stage') }}

union all
select -1, null, 'Unknown', null
