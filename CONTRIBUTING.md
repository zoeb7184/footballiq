# Contributing — Engineering Standards

## SDLC
Every module follows: Requirements → Architecture → Design → Implementation
→ Testing → Deployment → Monitoring → Documentation. No module is "done"
without its report in `docs/modules/` (template: `docs/templates/module-report.md`).

## Decisions
Architecturally significant decisions require an ADR (`docs/adr/`, see ADR-0001).

## Branching & commits
- Trunk-based: short-lived branches `feat/…`, `fix/…`, `docs/…` into `main`.
- Conventional Commits: `feat(api): add player valuation endpoint`.

## Quality gate (Definition of Done)
`make check` must pass — it runs:

1. `ruff check` — lint
2. `mypy` (strict) — types
3. `pytest` — tests with coverage

Pre-commit hooks handle formatting. CI runs the same `make check` (Module 9).

## Layering rules (ADR-0002)
`api → application → domains → kernel`; `infrastructure` implements
application ports. Imports against the arrows are defects.

## Repository organization
This repository favors **stability over cosmetic refactoring**. The layout
follows common Python and enterprise conventions:

- `src/` — application code (Clean Architecture layers).
- `tests/` — mirrors the source tree (`unit`, `integration`, `fixtures`).
- `docs/` — architecture, ADRs, specifications, module reports, reviews.
- `infra/` — deployment and infrastructure assets (Bicep, DB init).
- `portal/` — the Streamlit client (API-only).
- `transform/` — the dbt project.

Directories are not renamed or relocated solely for aesthetics. Any structural
change must (1) provide a measurable maintainability improvement, (2) update
every affected reference automatically, and (3) pass the full validation suite —
`make check`, `make demo`, CI, and documentation link verification. This keeps
paths stable and predictable for contributors, automation, and AI coding agents.

## Never commit
Secrets, `.env` files, datasets, files > 500 KB.
