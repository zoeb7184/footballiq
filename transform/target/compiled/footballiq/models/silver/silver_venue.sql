select
    venue_id::int             as venue_id,
    stadium_name              as stadium_name,
    city                      as city,
    country                   as country,
    capacity::int             as capacity,
    latitude::numeric(9, 4)   as latitude,
    longitude::numeric(9, 4)  as longitude,
    elevation_meters::int     as elevation_m
from "footballiq"."bronze"."raw_venues"
where 
    _load_id = (
        select load_id
        from "footballiq"."bronze"."_loads"
        where source_file = 'venues.csv'
        order by ingested_at desc
        limit 1
    )
