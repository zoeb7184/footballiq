select
    referee_id   as referee_sk,
    referee_id   as referee_id_nat,
    referee_name,
    country,
    avg_cards_per_game
from {{ ref('silver_referee') }}

union all
select -1, null, 'Unknown', null, null
