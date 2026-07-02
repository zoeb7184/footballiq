-- Grain: one player registered to one match (52/match incl. unused subs —
-- the source's grain, kept: participation, not events).
select
    l.lineup_id      as lineup_sk,
    l.match_id,
    f.date_key,
    l.player_id      as player_sk,
    l.team_id        as team_sk,
    l.is_starting_xi,
    l.tactical_position,
    l.minutes_played
from "footballiq"."silver"."silver_lineup" as l
inner join "footballiq"."gold"."fact_match" as f on l.match_id = f.match_id