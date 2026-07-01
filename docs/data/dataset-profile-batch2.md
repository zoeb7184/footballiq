# Dataset Profile — Batch 2 (players, events, stats, lineups)

> Measured 2026-07-02. Completes the 11-file profile (batch 1: matches core).

## Measured facts
- **squads_and_players (1,248):** PK unique, zero nulls. Exactly 48×26 squads.
  `market_value_eur` €25K–€200M, fully populated → **valuation label verified**.
  450 distinct clubs (feeds talent-flow graph, R2). Positions GK/DEF/MID/FWD.
  DOB range 1982–2008.
- **player_stats (1,248):** PK unique; FKs valid. `shots`, `shots_on_target`,
  `average_rating` 100% null → dead columns, bronze-only. GK fields null for
  1,103 outfielders → structural-by-position. `data_source` empty for 241
  rows → lineage default "unverified". Cumulative tournament aggregates,
  last_verified 2026-07-01.
- **match_team_stats (132):** 2 rows per covered match, but covers only
  **66 of 76 completed matches** → partial-coverage fact; coverage must be
  declared and logged. player_of_the_match populated once per match
  (reconciliation-only vs fact_match).
- **match_lineups (3,952):** perfectly regular 76×52 (26 per team incl.
  unused subs); starting XI = exactly 11 per team-match; zero nulls;
  all FKs valid. Grain = player registered to match.
- **match_events (583):** Goal 223, Yellow 194, Assist 152, Red 9, VAR 5.
  All FKs valid; only completed matches. **Goal counts reconcile with match
  scores exactly (0 mismatches)** → becomes a permanent pipeline check.
- Batch-1 loose ends closed: player_of_the_match FK resolves;
  matches_detailed goalkeepers derivable from lineups → file fully redundant
  (bronze-only reconciliation role confirmed).

## Leakage additions
1. Lineups, minutes, and cumulative player_stats are POST for the outcome
   model. player_tournament_snapshot = **BI-only, never an ML feature
   source**; per-match-cutoff aggregates derive from events+lineups (as-of).
2. market_value_eur snapshot date undocumented → valuation model declared
   **cross-sectional** (estimate value from attributes + observed
   performance), not temporal forecasting. Documented assumption.
