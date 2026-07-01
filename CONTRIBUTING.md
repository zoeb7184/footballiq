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

## Never commit
Secrets, `.env` files, datasets, files > 500 KB.
