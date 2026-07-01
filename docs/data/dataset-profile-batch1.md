# Dataset Profile — Batch 1 (matches core)

> Measured on actual files 2026-07-02. Files: teams, venues, tournament_stages,
> referees, matches, matches_detailed. Player/event/lineup files pending.
> Analysis of data as-is; no schema redesign.

## Measured facts
- 89 matches: 76 Completed (all with xG), 13 Scheduled (structural nulls in
  scores/xG/player_of_the_match — filter by `status`, never impute).
- Mid-tournament snapshot: group stage complete (72), Round of 32 in progress
  (4/16 completed), 1 R16 fixture. Dates 2026-06-11 → 2026-07-04.
- All PKs verified unique. All populated FKs verified intact.
- Match 89: empty `away_team_id` — legitimate TBD bracket slot; ingestion must
  model "opponent undetermined" (nullable FK), not reject the row.
- matches_detailed is score-consistent with matches; adds only
  home/away goalkeeper. Canonical source = matches.csv; detailed file used as
  reconciliation fixture + goalkeeper enrichment.
- teams: Elo 1510–2150, FIFA rank pre-tournament (static snapshots — no
  leakage as pre-match features). 12 groups × 4 teams.
- venues: 16 (USA 11 / MEX 3 / CAN 2); elevation up to 2,200 m (Azteca).
- referees: avg_cards_per_game 3.4–5.5 — pre-aggregated, provenance
  undocumented (lineage gap; record as externally computed metric).
- Dangling FK: matches.player_of_the_match_id → player registry (next batch).

## Classification
- **Fact:** matches (grain: one match; measures: scores, xG).
  matches_detailed = pre-joined consumption copy, not a second fact.
- **Dimensions:** teams (role-playing home/away), venues, stages, referees.
  `status` = degenerate dimension; date → date dimension at warehouse build.
- **Star schema:** emerges directly — fact_match + dim_team/venue/stage/referee
  (+ dim_player when player files land). matches_detailed is empirically the
  join product of this star.
- **Snowflake:** latent paths venue→country, team→confederation; deliberately
  flattened — cardinality (16/3, 48/6) doesn't justify sub-dimensions.

## ML readiness
- **Match outcome model:** labels from 76 completed matches. Hard caveats:
  small N; only 4 knockout labels; xG is post-match → target leakage if used
  as pre-match feature (allowed: lagged xG form, Elo/rank priors);
  home advantage confounded with host nations (USA/MEX/CAN).
  Knockout stages exclude draws → stage-conditional class space.
- **Player valuation model:** depends on squads_and_players.csv (not in this
  batch). matches contribute context only.

## Business glossary
Player = valued asset; Match = atomic operational event; Team = business unit
(asset portfolio); Venue = facility with operational covariates; Referee =
external compliance factor; xG = model-derived expected-performance KPI,
post-event information governed for leakage.
