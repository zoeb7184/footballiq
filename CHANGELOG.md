# Changelog

All notable changes to FootballIQ Enterprise. Format follows
[Keep a Changelog](https://keepachangelog.com); versioning follows SemVer
(0.x = pre-stable; minor = completed module group).

## [Unreleased]
- CI quality gate (GitHub Actions) with 80% coverage floor
- Multi-stage pipeline Dockerfile (non-root, one-image-many-jobs)
- Consolidated testing strategy; documentation map

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
