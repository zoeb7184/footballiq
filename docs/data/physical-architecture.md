# Physical Data Architecture — v2

> Translation of `logical-data-model.md` to physical design. No SQL/code —
> implementation lands in Module 2. Layers = database schemas (bronze/silver/
> gold) on one engine: governance per layer, not infrastructure we don't need.
> v2 (2026-07-02): extends v1 with the player/event/stats file family after
> batch-2 profiling (`dataset-profile-batch2.md`). fact_match unchanged.

## 1. Medallion layers
| Layer | Rule | Contents |
|---|---|---|
| bronze | Append-only, verbatim, immutable; stamped load_id, source file, hash, ingested_at | all source files incl. matches_detailed |
| silver | Typed, conformed, natural keys; contract checks; violations → quarantine (with reason); idempotent merge, status forward-only | match, team, venue, stage, referee |
| gold | Star + serving tables; only layer BI/API/ML read | fact_match, dim_*, features, predictions |

matches_detailed is **bronze-only**: reconciliation fixture (score/row-count
cross-check vs silver.match). Never in gold.
*(Amended per ARB 2026-07-02 finding M1a: the originally planned goalkeeper
enrichment was superseded — match_lineups provides goalkeepers at better
grain; the enrichment was never implemented and is formally dropped.)*

## 2. Warehouse schema
- **fact_match:** surrogate FKs, degenerate status, nullable measures,
  natural match_id for lineage; grain = uniqueness on match_id.
  Completed-row immutability enforced in pipeline pre-merge check, not triggers.
- **Dims:** integer surrogates (platform-generated), natural key retained,
  Type-1 overwrite. **Reserved members seeded with fixed keys:**
  −1 Unknown (all dims), −2 TBD (DimTeam only) — stable across environments.
- **DimDate:** generated calendar, key yyyymmdd.
- **TBD mapping:** silver keeps source null; gold load maps
  null-in-knockout → TBD(−2), otherwise → Unknown(−1). One translation point.

## 3. Fact family (v2 — expansion realized, non-breaking)
Rules held from v1: new facts join via conformed dims + existing match key;
**fact_match never widens**; no fact→fact surrogate coupling; every fact
declares grain + contracts before load code.

| Gold table | Grain | Source | Notes |
|---|---|---|---|
| fact_match | one match | matches | unchanged from v1 |
| fact_match_event | one event occurrence | match_events | types: Goal/Assist/Yellow/Red/VAR. Contract: Σ Goal events per match = fact_match scores (verified 0 mismatches → permanent pipeline check) |
| fact_match_team_stats | team-match (2/match) | match_team_stats | **partial coverage declared** (66/76 completed at profiling); coverage % logged per load; BI must not assume completeness |
| fact_player_match | player registered to match (52/match incl. unused subs) | match_lineups | measures: minutes; is_starting_xi degenerate; participation, not events |
| player_tournament_snapshot | player-tournament | player_stats | source-precomputed aggregate; reconciled vs events+lineups (base facts win, discrepancies logged); **BI-only, never an ML feature source** |

Silver promotion exceptions: player_stats dead columns (shots,
shots_on_target, average_rating — 100% null) stay bronze-only; GK-only
fields structural-null by position; data_source defaults to "unverified".

### DimPlayer (finalized, was deferred)
Platform surrogate + natural player_id; 1,248 real members + Unknown(−1).
Attributes: name, position (GK/DEF/MID/FWD), date_of_birth (age derived at
query time, never stored), height_cm, caps, international_goals, club_team
(string attribute — no dim_club in MVP; 450 clubs noted as future
extension), national-team FK to dim_team, market_value_eur (Type-1 numeric
attribute; also the valuation model label).
Roles: Player of the Match (fact_match), participant (fact_player_match),
event actor (fact_match_event).

## 4. ML feature layer
- **gold.feature_match_prematch:** one row per match per feature_version;
  only PRE + DERIVED-ASOF columns; carries cutoff_ts (kickoff).
- **Feature registry:** name, availability tag, formula owner per feature.
- **Leakage enforcement:** (a) builder input pre-filtered to < cutoff;
  (b) CI test recomputes historical features at cutoff, asserts equality;
  (c) POST columns not joinable in feature path.
- **Training vs inference:** one pipeline, two consumers. Training =
  features ⋈ labels (completed); inference = scheduled matches (TBD excluded).
  Models stamped with feature_version.
- **v2 leakage additions:** lineups/minutes/cumulative player stats are POST
  for the outcome model — per-match-cutoff player aggregates derive from
  fact_match_event + fact_player_match (as-of), never from
  player_tournament_snapshot. Valuation model declared **cross-sectional**
  (market_value snapshot date undocumented): estimates value from attributes
  + observed performance; not a temporal forecast. dim_player registry
  attributes (value, caps, age, height) are PRE for the outcome model.

## 5. BI layer (Power BI)
- Semantic model reads **gold only**; import mode (small data, full DAX).
- fact→dim single-direction; DimTeam role-playing: active relationship =
  home, inactive = away (per-measure activation); alias views as fallback.
- KPI layer: measures defined once in semantic model, mirrored in
  docs/bi/kpis.md (API and BI must not disagree on formulas).
- Dashboard 1 (Executive Squad Overview) ← fact_match, dim_team, dim_stage
  (+ squad value aggregates post-batch-2).
  Dashboard 2 (Talent Valuation Intelligence) ← dim_player + gold prediction
  table (batch-2 dependent by design).

## 6. API mapping
- **Exposed (/v1, gold read models):** teams; schedule/results (status-aware);
  predictions with explanations (valuation+SHAP, outcome probabilities);
  players (post-batch-2); health/metadata.
- **Internal only:** bronze/silver, quarantine, feature tables, model
  registry, reconciliation reports.
- **Contracts at the edge:** DTOs mirror data contracts — Scheduled DTO has
  no score fields (not null scores); TBD = explicit enum state; every
  prediction response carries model + feature version.
