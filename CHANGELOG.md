# Changelog

All notable changes to FootballIQ Enterprise. Format follows
[Keep a Changelog](https://keepachangelog.com); versioning follows SemVer
(0.x = pre-stable; minor = completed module group).

## [Unreleased]

## [0.5.0] — 2026-07-04
### Added
- **Module 5 — ML + explainable AI (SHAP):** cross-sectional player valuation
  model with per-player SHAP explanations, served as prediction-as-data. Four
  vertical slices — feature store, gated trainer, batch scoring, serving —
  each with tests and lineage. Honest metrics reported as-is (RMSLE 0.937 vs
  0.942 linear / 1.698 median; MdAPE ~50%; ~20% within +/-20%).
- **M5 Slice 4 — valuation serving (ML design §9):** `GET /v1/valuations`
  (sortable by value_gap / predicted_value / market_value — value_gap desc is
  the scout shortlist), `GET /v1/players/{id}/valuation` (headline top-k),
  `GET /v1/players/{id}/valuation/explanation` (full breakdown + baseline).
  Every response carries model_version + feature_version + scored_at and an
  accuracy note; unscored/unknown player is an explicit 404, never a fake value
- Readiness now requires a scoring run: `/ready` reports not-ready (503) until
  `gold.prediction_player_valuation` is populated (`make score`)
- Dashboard 2 value-gap SQL catalog: shortlist, gap-by-position, and a
  per-player SHAP tornado/bridge drill-through query
- **M5 Slice 3 — SHAP batch scoring (XAI design §§2-4):** `make score`
  loads `gold.prediction_player_valuation` (predicted_value_eur,
  value_gap_eur = predicted − market, denormalized top-k SHAP payload) and
  `gold.explanation_player_valuation` (long format: player × feature,
  shap_log canonical, multiplicative_factor = exp(φ), rank, baseline) in one
  atomic transaction — an explanation cannot exist without its prediction
- TreeSHAP via the booster's own `pred_contribs` in log1p space (the
  trainer's fit space), so `base + Σφ` reconstructs the model margin exactly
- **Write-time additivity invariant:** an independently computed margin must
  equal `base + Σφ` within tolerance for every player, or the whole load is
  refused (`ScoringAdditivityError`)
- Registry getter `load_production_model` pins each scoring run to the served
  model_version + feature_version; a feature-table version mismatch fails
  fast (`FeatureVersionMismatch`) before any scoring

## [0.4.0] — 2026-07-02
### Added
- **Module 4 — BI dashboards (Metabase, ADR-0005):** Executive Squad
  Overview (KPI cards, value-vs-performance quadrant, rankings, xG
  over/underperformance) and Talent Valuation Intelligence (age-value
  curve, top-25, value by position)
- Metabase compose service connecting as the grant-locked `fiq_api` role
  (gold-only BI, verified)
- Versioned KPI SQL catalog (`docs/bi/queries/`) — one truth per KPI,
  shared BI/API (parity mechanism operational; 76/223 verified live)
### Changed
- ADR-0005: Metabase replaces Power BI (macOS constraint); BI design docs
  annotated, remain tool-portable

## [0.3.0] — 2026-07-02
### Added
- **Module 3 — FastAPI backend:** query-only read API over gold —
  /health, /ready (refuses to serve without data), /v1/teams,
  /v1/matches, /v1/players; four-layer DI (routers → queries → ports →
  gold adapters) with composition root in api/main
- Status-discriminated match contract: ScheduledMatch structurally
  scoreless; CompletedMatch requires score+xG; TBD opponent as typed state
- API-key auth: sha256-hashed keys, constant-time compare, default-deny
- RFC 7807 problem+json errors with correlation IDs
- Postgres integration test ring + CI service container (ARB H1)
- CI quality gate (GitHub Actions) with 80% coverage floor; multi-stage
  pipeline Dockerfile; testing strategy + documentation map;
  Architecture Review Board report
### Fixed
- ARB drift findings: dotenv loader; matches_detailed doc annotation;
  coverage omit for CLI wrappers

## [0.2.0] — 2026-07-02
### Added
- **Module 2 — Data platform:** docker-compose Postgres warehouse with
  schema/role init (gold-only API grant); idempotent bronze ingestion
  (load registry, sha256 no-op detection); dbt silver layer with
  quarantine-with-reasons; gold star schema (6 dims with reserved members,
  4 facts + snapshot); 68 executable data contracts incl. goal-sum,
  matches_detailed, and grain reconciliations; known-issues registry
- **Module 1 — Domain core:** kernel (Entity, ValueObject, Result, ports);
  football entities with lifecycle invariants (typed TBD opponent,
  forward-only match, knockout no-draw); import-linter layer contract
- MIT license; data setup documentation
### Fixed
- Snapshot goal reconciliation accounts for own-goal attribution
  (root-caused: event log credits own goals to the scorer)
- Player-887 source attribution defect registered in known-issues registry

## [0.1.0] — 2026-07-02
### Added
- Module 0 — Foundation: clean-architecture scaffold, ADRs 0001–0004,
  quality tooling (ruff, mypy strict, pytest, pre-commit)
- Design corpus: scope/PRD, dataset profiles, logical + physical data
  models, ML/XAI/graph/backend/BI/RAG/Azure designs
