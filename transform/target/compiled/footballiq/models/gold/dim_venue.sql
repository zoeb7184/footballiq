select
    venue_id     as venue_sk,
    venue_id     as venue_id_nat,
    stadium_name,
    city,
    country,
    capacity,
    latitude,
    longitude,
    elevation_m
from "footballiq"."silver"."silver_venue"

union all
select -1, null, 'Unknown', null, null, null, null, null, null