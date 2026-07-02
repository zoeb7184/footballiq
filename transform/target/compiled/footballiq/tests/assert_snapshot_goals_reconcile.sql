-- Snapshot vs base facts: per-player goals in the source-precomputed
-- snapshot should match Goal events. WARN severity — on disagreement the
-- base facts win and the discrepancy is investigated, not hidden
-- (physical architecture §3).


with event_goals as (
    select player_sk, count(*) as goals_from_events
    from "footballiq"."gold"."fact_match_event"
    where event_type = 'Goal'
    group by player_sk
)

select
    s.player_sk,
    s.goals                              as snapshot_goals,
    coalesce(e.goals_from_events, 0)     as event_goals
from "footballiq"."gold"."player_tournament_snapshot" as s
left join event_goals as e on s.player_sk = e.player_sk
where s.goals != coalesce(e.goals_from_events, 0)