-- Snapshot vs base facts, per player.
--
-- DEFINITION (root-caused 2026-07-02, 9-player investigation): the event log
-- attributes own goals as 'Goal' events to the scoring player (so match-score
-- reconciliation sums correctly), while the snapshot separates `goals` from
-- `own_goals`. Therefore the reconciliation identity is:
--     snapshot.goals + snapshot.own_goals = count(Goal events)
-- WARN severity: on a true disagreement, base facts win and the discrepancy
-- is investigated, not hidden (physical architecture §3).
{{ config(severity='warn') }}

with event_goals as (
    select player_sk, count(*) as goals_from_events
    from {{ ref('fact_match_event') }}
    where event_type = 'Goal'
    group by player_sk
)

select
    s.player_sk,
    s.goals                          as snapshot_goals,
    s.own_goals                      as snapshot_own_goals,
    coalesce(e.goals_from_events, 0) as event_goals
from {{ ref('player_tournament_snapshot') }} as s
left join event_goals as e on s.player_sk = e.player_sk
where s.goals + s.own_goals != coalesce(e.goals_from_events, 0)
