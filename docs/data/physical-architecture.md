# Physical Data Architecture — v1

> Translation of `logical-data-model.md` to physical design. No SQL/code —
> implementation lands in Module 2. Layers = database schemas (bronze/silver/
> gold) on one engine: governance per layer, not infrastructure we don't need.

## 1. Medallion layers
| Layer | Rule | Contents |
|---|---|---|
| bronze | Append-only, verbatim, immutable; stamped load_id, source file, hash, ingested_at | all source files incl. matches_detailed |
| silver | Typed, conformed, natural keys; contract checks; violations → quarantine (with reason); idempotent merge, status forward-only | match, team, venue, stage, referee |
| gold | Star + serving tables; only layer BI/API/ML read | fact_match, dim_*, features, predictions |

matches_detailed is **bronze-only**: reconciliation fixture (score/row-count
cross-check vs silver.match) + goalkeeper enrichment. Never in gold.

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

## 3. Future fact expansion (non-breaking rules)
Declared grains: fact_match_event (event occurrence), fact_match_team_stats
(team-match), fact_player_match (player-match, from lineups).
Rules: new facts join via conformed dims + existing match key;
**fact_match never widens**; no fact→fact surrogate coupling; every new fact
declares grain + contracts before load code. player_stats.csv = source
aggregate (player-tournament grain): gold snapshot reconciled against
event-derived numbers; base facts win, discrepancies logged.

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
