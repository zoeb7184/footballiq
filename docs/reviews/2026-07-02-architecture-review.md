# Architecture Review Board — 2026-07-02 (v0.2.0, pre-Module-3)

> Scope of review: modules 0–2 as built; modules 3–9 as designs only.
> The board does not grade paper as product.

## Findings

### Critical
- **C1 — Platform 33% implemented.** API/BI/ML/XAI/graph/RAG/portal/deploy
  are specifications. Value propositions undeliverable today.
  Fix before release: **yes — building them is the release.**

### High
- **H1 — CI never touches real Postgres.** Loader tests on SQLite; dbt
  tests local-only (CI runs parse). Silent PG-specific regressions possible.
  Fix: PG service container + fixture-based dbt build/test in CI. Binding
  for M3.
- **H2 — Secrets local-grade, partially committed.** Acceptable per
  ADR-0003; add "committed credentials are local fixtures; cloud generates
  fresh via Key Vault (M9)" note. Binding before any cloud deploy.

### Medium
- **M1 — Design/code drift ×2:** (a) matches_detailed goalkeeper enrichment
  designed, superseded by lineups — annotate doc; (b) .env.example implies
  dotenv loading config.py doesn't do — implement or reword. Cheap; fix now.
- **M2 — Row-by-row bronze inserts.** Fine at 7.4K rows; documented ceiling.
- **M3 — Coverage config vs strategy:** __main__ modules still counted;
  apply omit-with-comment during M3 restructure.
- **M4 — DR never rehearsed.** One timed PITR restore with the M9 runbook.

### Low / Observations
- L1 kernel Result/ports consumer-less until M3 (flagged, acceptable).
- L2 composition-root placement (api vs infrastructure) — decide in M3.
- L3 solo direct-to-main; one PR-merged module would show workflow.
- **Strengths recorded:** grant-enforced access; known-issues registry;
  own-goal/player-887 forensic trail; reserved members; dev/CI parity;
  scope.md repelled four expansion attempts; measured-data-first design.

## Scores
| Dimension | /10 |
|---|---|
| Architecture quality | 8.5 |
| Production readiness | 3 (complete ≠ grade: what exists is release-quality) |
| Portfolio quality | 7 (nothing visual/experienceable yet) |
| Enterprise maturity | 8 |

## Hiring signal
Junior: far exceeds. Mid: strong, evidenced. Senior: strong trajectory,
case completes when MVP ships (senior = delivered, not designed).
Staff: instincts visible; category requires organizational impact a solo
project cannot show.

## Top 5 ROI
1. Build Module 3 (converts design credibility → product credibility).
2. PG container + fixture dbt tests in CI (closes H1).
3. One visual artifact per module from M3 (portfolio gap).
4. Drift repairs (M1) — an hour that preserves doc authority.
5. `make demo` E2E as soon as M3 lands.

## Verdict
**Not production-ready — by incompleteness, not deficiency.** Delivered
scope is release-quality; no architectural obstacle identified for the
remaining modules. Disposition: **proceed to Module 3; reconvene at MVP.**
