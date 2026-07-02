# Backend Architecture — v1

> Endpoint contracts are settled elsewhere (physical §6, ML design §9,
> XAI §5). This document designs the backend internals that serve them.
> Constraints: prediction-as-data, gold-only reads, versioned contracts.

## 1. Query-only backend (CQRS, no C)
All writes happen in batch pipelines. The API is exclusively the query
side: no POST/PUT for domain data exists in MVP — the API cannot mutate
gold even in principle. Commands (trigger rescore, upload) = future
extensions.

## 2. Layering (ADR-0002 applied)
api/routers (HTTP only) → application/queries (GetPlayerValuation,
ListValueGaps, …) → application/ports (typed ReadModel protocols) →
infrastructure/gold (SQL adapters). Binding via FastAPI DI at startup.
Nothing above infrastructure knows SQL exists.

## 3. Gold-only as a database grant
API role: SELECT on gold schema, no other privileges. The bronze/silver
prohibition is engine-enforced, not convention. Illegal states
unrepresentable, at the permission layer.

## 4. DTOs: contracts as types
- Discriminated union by status: ScheduledMatch has no score fields;
  CompletedMatch requires them; TBD = enum state.
- not_predictable = typed 200 business state with reason (never null,
  never an error).
- Every prediction/explanation DTO: model_version, feature_version,
  scored_at.
- /v1 prefix; additive-only within v1; breaking ⇒ /v2. DTO layer decouples
  gold evolution from clients.

## 5. Auth & cross-cutting (anti-scope-sized)
- API-key header; hashed storage; constant-time compare; per-key rate limit
  middleware. No OAuth/RBAC (documented extension points).
- Errors: RFC 7807 problem+json; 404 / 422 / 500-with-correlation-ID.
- Observability: structured JSON logs, request IDs, OpenTelemetry with
  console exporter locally → Azure Monitor per ADR-0003.
- OpenAPI generated from typed DTOs (docs cannot drift).
- /health (liveness); /ready verifies gold tables **and a scoring run
  exist** — no predictions ⇒ not ready, never empty shortlists.

## 6. Performance posture
Connection pool; pagination with hard max everywhere; HTTP caching keyed
to batch cadence (Last-Modified = latest scored_at; ETag = run ID).
No app cache layer in MVP.

## 7. Testing rings
1. Router tests with fake ports (no DB): HTTP semantics, auth, errors.
2. Adapter tests vs seeded test DB: SQL + DTO mapping.
3. Contract tests vs OpenAPI schema + invariants (completed ⇒ scores;
   versions always present; scheduled structurally scoreless) — each
   citing the data-contract doc section it enforces.
