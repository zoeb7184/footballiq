-- Grain: one event occurrence (Goal / Assist / Yellow / Red / VAR Review).
select
    e.event_id       as event_sk,
    e.match_id,
    f.date_key,
    e.team_id        as team_sk,
    e.player_id      as player_sk,
    e.minute,
    e.event_type
from "footballiq"."silver"."silver_match_event" as e
inner join "footballiq"."gold"."fact_match" as f on e.match_id = f.match_id