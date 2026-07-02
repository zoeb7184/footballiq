-- Source-precomputed player-tournament aggregate. BI-only: never an ML
-- feature source (ML design §2B). Reconciled against base facts —
-- see assert_snapshot_goals_reconcile (base facts win on disagreement).
select
    s.player_id      as player_sk,
    s.team_id        as team_sk,
    s.matches_played,
    s.matches_started,
    s.minutes_played,
    s.goals,
    s.assists,
    s.yellow_cards,
    s.red_cards,
    s.penalty_goals,
    s.own_goals,
    s.clean_sheets,
    s.saves,
    s.goals_conceded,
    s.data_source,
    s.last_verified
from {{ ref('silver_player_tournament_stats') }} as s
