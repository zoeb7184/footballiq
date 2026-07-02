select
    referee_id::int                      as referee_id,
    name                                 as referee_name,
    country                              as country,
    avg_cards_per_game::numeric(4, 2)    as avg_cards_per_game
from {{ source('bronze', 'raw_referees') }}
where {{ latest_load('referees.csv') }}
