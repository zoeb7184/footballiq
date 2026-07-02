# Module 3 — FastAPI Backend

## 1. Requirements
Query-only read API over gold implementing `docs/api/backend-design.md`:
grant-locked access, contracts as types, RFC 7807 errors, readiness that
refuses to serve without data.

## 2. Architecture
Four layers per ADR-0002: routers (HTTP only) → application queries →
read-model ports → gold adapters. **Composition root = `api/main.py`**
(ARB L2 resolved): the outermost layer wires settings → engine → adapters.
Endpoints: /health, /ready, /v1/teams, /v1/matches, /v1/players — all /v1
guarded by API-key auth; system endpoints open for orchestrator probes.

## 3. Design rationale
- **Status-discriminated match DTO:** ScheduledMatch has no score/xg fields
  (structurally scoreless); CompletedMatch requires them; the away side of
  a scheduled match is `TeamRef | TbdOpponentRef` — TBD is a typed state,
  never a null. Contract violations in gold (impossible per dbt tests,
  guarded anyway) raise → 500: loud, never a silent half-answer.
- **Auth default-deny:** sha256-hashed keys, constant-time compare; zero
  configured keys ⇒ all requests rejected. Dev key ships as a hash in
  .env.example only.
- **Reserved members (sk < 0) excluded at adapters** — join semantics,
  not catalog entries.
- **Readiness phased:** M3 checks warehouse + populated fact_match; the
  scoring-run check (backend §5) activates in M5 when predictions exist.
- Scout-first player ordering (market value desc); DOB shipped raw (age
  derived by consumers — DimPlayer rule).
- Valuation/prediction endpoints deliberately absent: they serve M5's
  tables (serving contract, ML design §9).

## 4. Implementation
5 slices: (1) drift repairs + skeleton + problem+json + health/ready via
ReadinessProbe port; (2) teams vertical + auth + PG integration ring + CI
service container (ARB H1); (3) matches with discriminated union over a
5-way star join; (4) players with filters; (5) release wrap.

## 5. Testing
**Validated on host (Python 3.12): 59 passed + 2 integration (CI-run),
95.6% coverage, mypy strict, import-linter KEPT (46 edges).**
Ring 1: fake-port router tests (auth paths, pagination hard-max 422,
discriminated shapes, TBD-as-state, violation-to-500). Ring 1.5: SQLite
star fixtures for adapters (ordering, filters, reserved-member mapping).
Ring 2: real-Postgres tests (isolated it_* schemas) in CI's service
container. Verified visually: OpenAPI docs, live match 89 TBD response,
value-ordered player registry.

## 6. Future improvements
- schemathesis property-based fuzzing from the OpenAPI spec (testing
  strategy; slot: with M5's endpoint additions)
- Rate limiting middleware (designed, backend §5; slot: M9 hardening)
- HTTP caching keyed to scoring runs (backend §6; needs M5 run metadata)
- teams.py adapter local coverage via sqlite fixture (currently CI-only)

---

## Portfolio annex
- **Skills demonstrated:** FastAPI + DI via typed ports, discriminated
  unions as API contracts, secure-by-default auth, two-ring DB testing,
  OpenAPI-from-types, CQRS query side.
- **Interview questions prepared:** "How do you make an API contract
  unbreakable?" "Where does DI wiring belong?" "How do you test adapters
  without mocking SQL?" "Why default-deny auth?"
- **Enterprise concepts applied:** contracts as types, grant-enforced
  access, probes vs liveness, composition root, prediction-as-data
  (the API cannot run models — there are none to run).
- **Resume bullet:** "Built a query-only FastAPI backend over a governed
  warehouse: status-discriminated DTOs that make invalid responses
  unrepresentable, hashed default-deny API-key auth, port/adapter DI, and
  a two-ring test suite (fake ports + real Postgres in CI) at 95% coverage."
- **LinkedIn:** "v0.3.0: FootballIQ has an API. Favorite contract: a
  scheduled match structurally cannot carry a score — the field doesn't
  exist on the type. And match 89's undetermined opponent is an explicit
  typed state, not a null."
