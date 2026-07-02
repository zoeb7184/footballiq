select
    venue_id::int             as venue_id,
    stadium_name              as stadium_name,
    city                      as city,
    country                   as country,
    capacity::int             as capacity,
    latitude::numeric(9, 4)   as latitude,
    longitude::numeric(9, 4)  as longitude,
    elevation_meters::int     as elevation_m
from {{ source('bronze', 'raw_venues') }}
where {{ latest_load('venues.csv') }}
