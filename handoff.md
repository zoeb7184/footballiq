# FootballIQ Enterprise — Engineering Handoff

> Authoritative context for continuing this project in a fresh session. Read
> this fully before acting. Represents the repository's current state, not a
> changelog (see CHANGELOG.md / git log for history).

## Project Goal
A domain-agnostic **AI decision-intelligence platform**, demonstrated on football
analytics. Football is only the demo domain — the architecture retargets to any
industry by swapping the `domains/` package and ingestion adapters. It spans a
medallion data warehouse, a versioned API, explainable ML, graph analytics, a
grounded RAG assistant, a customer portal, and cloud-deployable IaC — built to
show production engineering practices end to end.

> **Update (2026-07-18):** Module 10 (simulation + model governance,
> ADR-0006) and the production Next.js web app (`web/`) were added on top of
> v1.0.0; version bumped to 1.1.0. See CHANGELOG `[1.1.0]`,
> `FRONTEND_BLUEPRINT.md`, `docs/modules/10-simulation.md`, and
> `docs/deployment-free-tier.md`. Host verification pending: run
> `make check` and the web quality gate (see README) before tagging v1.1.0.

## Current Status
- **Version:** 1.1.0 (in working tree; tag after host `make check` passes).
- **Completed modules:** M0 foundation, M1 domain core, M2 data platform
  (medallion + dbt, 68 contracts), M3 FastAPI, M4 Metabase BI, M5 ML+SHAP,
  M6 graph analytics, M7 RAG analyst, M8 Streamlit portal, M9 ship (Docker/
  CI-CD/Bicep/demo).
- **Branch:** `main`
- **Latest commit:** `c62341e` — "docs: add Kaggle dataset link + expected file
  list to README"
- **Latest tag:** `v1.0.0`
- **Working tree:** clean; `main` is in sync with `origin/main` (all pushed).
- **Quality gate:** `make check` green — ruff, mypy (strict), import-linter
  (ADR-0002 layers KEPT), 129 tests pass / 2 skipped, 92% coverage.

## Current Task
None in progress. The project is complete and released at v1.0.0; the working
tree is clean and pushed. The last activity was documentation finalization
(README polish, dataset link, org policy) and making the dormant deploy workflow
skip cleanly until Azure is configured.

## Files Modified This Session
This was a long session that delivered Modules 6–9 plus documentation. Grouped
by area (all committed):

- **M6 graph** — `src/footballiq/graph/*` (NetworkX build + CLI),
  `infrastructure/gold/graph.py`, `api/routers/graph.py`, read models/queries,
  BI graph SQL, `docs/modules/06-graph.md`. Purpose: club↔nation talent-flow
  metrics served read-only.
- **M7 RAG** — `src/footballiq/application/rag/*` (chunking, indexing, routing,
  grounding, pipeline, ports), `infrastructure/ai/*` (embeddings, vector_store,
  fact_provider, retriever, query_log, index CLI), `api/routers/analyst.py`,
  `infra/postgres/init/02-ai-schema-and-role.sql`, `docs/modules/07-ai.md`.
  Purpose: grounded single-turn analyst (numbers from SQL only).
- **M8 portal** — `portal/*` (api_client, session, app, 3 pages),
  `tests/unit/test_portal_client.py`, `docs/modules/08-portal.md`. Purpose:
  Streamlit client over the public API only.
- **M9 ship** — `Makefile` (`demo`, `graph`, `ai-up`, `index`, `portal`
  targets), `scripts/demo_smoke.py`, `infra/bicep/*`,
  `.github/workflows/deploy.yml`, `docs/runbook.md`, `docs/modules/09-ship.md`.
  Purpose: one-command demo + Azure IaC + deploy pipeline + runbook.
- **Cross-cutting** — `pyproject.toml` (extras: graph/rag/portal; version 1.0.0;
  ruff/mypy config), `docker-compose.yml` (image → `pgvector/pgvector:pg16`),
  `CHANGELOG.md`, `README.md` (flagship polish + demo guide + dataset link),
  `CONTRIBUTING.md` (repo-organization policy), `src/footballiq/__init__.py`
  (version).

## New Files Created
- `handoff.md` (this file).
- `docs/runbook.md`, `docs/modules/06–09-*.md` — ops + module reports.
- `infra/bicep/{main.bicep,staging.bicepparam,README.md}` — Azure IaC.
- `infra/postgres/init/02-ai-schema-and-role.sql` — ai schema, pgvector,
  fiq_analyst role, ai.query_log.
- `scripts/demo_smoke.py` — end-to-end smoke check for `make demo`.
- `.github/workflows/deploy.yml` — deploy pipeline (dormant until Azure vars set).
- `portal/*`, `src/footballiq/graph/*`, `src/footballiq/application/rag/*`,
  `src/footballiq/infrastructure/ai/*`, and their tests.

## Files Intentionally Left Unchanged
- **Repository structure** — reviewed in a dedicated audit; NOT reorganized. The
  layout is already conventional (`src/`, `tests/`, `docs/`, `infra/`, `portal/`,
  `transform/`, `.github/`). Moving `infra/`, `Dockerfile`, `docker-compose.yml`,
  or `scripts/` would break the compose init-mount, docker build context,
  Makefile, and CI for cosmetic gain. Policy recorded in `CONTRIBUTING.md`.
- `docs/data/*` raw CSVs — never committed by design (`.gitignore`); data lives
  in storage, git holds code.

## Decisions Made
- **Graph = NetworkX in batch, no graph DB** (~500 nodes / ≤1,248 edges). Metrics
  are analytics products, not ML features (future extension).
- **RAG: numbers from SQL only.** Semantic retrieval finds definitions; a
  `FactProvider` runs per-route SQL for every figure; a groundedness check
  rejects any numeric token not in tool evidence. Deterministic keyword routing
  (reproducible/CI-checkable); LLM behind an `LLMClient` port with a template
  default (no key required today).
- **pgvector in the existing Postgres** (image → `pgvector/pgvector:pg16`, same
  PG16, data volume reused). Local bge-small embeddings (free, CPU).
- **Least privilege + audit** — `fiq_analyst` role reads gold+ai only;
  `ai.query_log` makes every answer reconstructible.
- **Portal is API-only** — no `footballiq` import, no DB driver; proves contract
  sufficiency. Logic lives in a tested httpx client; pages are thin views.
- **M9 = placement, not redesign** — Bicep implements the committed Azure design
  (ADR-0003); portfolio tier (public + TLS + firewall), production hardening
  documented as the next step.
- **Cross-confederation graph metric deferred** — no club→confederation mapping
  in the warehouse (data-infeasible in MVP).

## Problems Encountered (and resolution)
- **Sandbox has no PyPI** — the assistant cannot run `make check`/`pytest`/
  `make demo`; the USER runs them on the host and pastes output. Every slice was
  self-checked (py_compile, line-length, lint-trap scan) then validated on host.
- **Assistant sandbox Python is 3.10** (host is 3.12) — `StrEnum` import fails in
  sandbox; verified logic standalone instead.
- **`.git` mount blocked writes early on** — commits/pushes are done by the USER
  on the host, not the assistant.
- **Recurring lint traps** (fixed each time): import ordering (ruff sorts
  `RetrievedChunk` before `Retriever`), `PLR2004` magic values (use named
  constants), `PLC0415` lazy imports (per-file-ignore for ml/* and ai/*),
  `RUF001/002` confusable unicode (avoid `×`, `·`; `—`/`§`/`±` are safe),
  `ARG002` unused args (noqa on the parameter line, not the def line),
  `RUF046` `int(round())` redundancy, `N999` (per-file-ignore for
  `portal/pages/*` numeric filenames).
- **Test-fixture colon collision** — inline JSON/timestamps in `text()` SQL were
  misparsed as bind params; fixed by binding those values as parameters.
- **BI `ROUND(double, n)` fails on Postgres** — prediction columns are
  DOUBLE PRECISION; cast `::numeric` before `ROUND` (fixed in BI SQL).
- **Deploy workflow showed red staging failures** — it reached for Azure that
  isn't provisioned; gated both deploy jobs on `vars.AZURE_CLIENT_ID != ''` so
  they skip cleanly until configured.

## Validation Performed
Run by the USER on the host (assistant cannot run them):
- `make check` — **PASSED** (ruff + mypy strict + import-linter + pytest,
  129 passed/2 skipped, 92% coverage). Green after every module.
- `make demo` / `make features` / `make train` / `make score` / `make graph` /
  `make ai-up` / `make index` — **PASSED** on real data (1,248 players scored;
  957 graph edges; 226 doc chunks indexed).
- `make api` (:8000), `make portal` (:8501), `make bi-up` (:3000) — **verified
  live** in the browser (Swagger, portal pages, Metabase dashboards, grounded
  analyst answers).
- `az bicep build` — **NOT executed** (needs Azure CLI); IaC is syntactically
  authored, validation left to the user/CI `validate-iac` job.

## Remaining Work
The project is complete. Only OPTIONAL polish remains, in priority order:
1. Create a **GitHub Release** for the `v1.0.0` tag using the CHANGELOG `[1.0.0]`
   notes.
2. Add **screenshots / a short demo recording** to the README (portal, Swagger,
   Metabase) for reviewers.
3. (If desired) a real **Azure staging deploy**: provision RGs + OIDC app, set
   repo vars `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_SUBSCRIPTION_ID`/
   `ACR_NAME` + secret `PG_ADMIN_PASSWORD`; the deploy workflow then activates.
4. (Optional, cosmetic) move `docs/runbook.md` → `docs/runbooks/` and
   `docs/infra/azure-architecture.md` → `docs/deployment/`, updating ~8
   cross-references + re-running `make index`. Build-safe; low value.

## Next Recommended Action
There is no blocking work. If continuing, start with the GitHub Release for
v1.0.0 (fastest reviewer-facing win), then README screenshots. Do NOT begin new
modules or restructure the repo — the scope is complete and `scope.md` governs
additions (an ADR is required to add scope). Any change must keep `make check`
green and the import-linter contract intact.

## Important Context
- **Environment:** macOS host, Python 3.12, `.venv` at repo root. Install extras
  before running data/ML/RAG/portal targets:
  `pip install -e ".[dev,rag,portal]"`.
- **Required services (three terminals + Docker):** `make db-up` (warehouse,
  Docker `pgvector/pgvector:pg16`), `make api` (:8000), `make portal` (:8501,
  needs API up first), `make bi-up` (:3000, Docker).
- **First-run order:** `make db-up` → `make pipeline` → `make demo` (or the
  individual targets) → start services. `make ai-up` must run once (creates the
  `ai` schema, pgvector, `fiq_analyst`, `ai.query_log`) before `make index` and
  the analyst endpoint.
- **Data is not in git.** Download from the Kaggle FIFA World Cup 2026 dataset
  (link in README) into `data/raw/` — 11 files declared in
  `src/footballiq/infrastructure/ingestion/manifest.py`.
- **Dev API key:** `dev-local-key` (Authorize in Swagger). DB URL:
  `postgresql+psycopg://fiq:fiq_local_dev@localhost:5432/footballiq`;
  roles `fiq_api`/`fiq_analyst` are gold(+ai)-only.
- **Conventions:** one vertical slice at a time; tests with every slice;
  Conventional Commits; `make check` green before proceeding; each module ships a
  report in `docs/modules/`, a CHANGELOG entry, README roadmap tick, version bump
  + git tag. The USER runs `make check`/commits on the host.
- **Known non-issues:** deploy workflow is dormant (skips until Azure vars set);
  `fact_provider`/`vector_store`/`embeddings`/`query_log` show low unit coverage
  by design (integration-only); portal is ruff-linted + client-tested but not
  under mypy.

## Disk Cleanup (post-v1.0.0)
Freed ~4 GB safely: removed stray venvs `.venv-1`/`.venv-2`, caches
(`.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.import_linter_cache`),
`transform/target`+`logs`, `__pycache__`, `.coverage`; `docker compose down` +
`docker image prune -a` (−2.76 GB images). All regenerate/re-pull on demand.
Kept: `.venv` (1.8 GB), `data/raw/`, `artifacts/`, `.git`, Docker volumes (hold
Metabase dashboards + warehouse). Optional further: `python3 -m pip cache purge`,
`rm -rf ~/.cache/huggingface`, `rm -rf .venv` (recreate via
`python3 -m venv .venv && pip install -e ".[dev,rag,portal]"`). Note: images were
pruned, so `make db-up`/`bi-up` re-download pgvector+Metabase (~2.76 GB).

## Session Summary
- Delivered Modules 6–9, taking the project from v0.5.0 to a complete **v1.0.0**.
- M6: NetworkX club↔nation talent-flow graph (supplier degree, HHI) + API + BI.
- M7: grounded RAG analyst (pgvector + local embeddings) — every number traces to
  SQL — with routing, a groundedness check, an LLM seam, audit log, and a
  least-privilege role.
- M8: API-only Streamlit portal (Scout Shortlist, Talent Flow, Ask the Analyst).
- M9: `make demo` + smoke check, multi-stage Docker, deploy workflow, Bicep IaC,
  and an operations runbook.
- Polished the README into a flagship open-source README (three-service demo
  guide, structured quickstart, reviewer flow, grouped docs, dataset link).
- Ran a repository-structure audit → recommended and made NO structural moves;
  codified the stability policy in CONTRIBUTING.md.
- Fixed the deploy workflow to skip cleanly until Azure is configured.
- `make check` green throughout; all work committed and pushed; released v1.0.0.
- Confirmed data is correctly excluded from git; added the Kaggle source link.
