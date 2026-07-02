# Testing Strategy — consolidated reference

> Consolidates by reference; adds only undecided items. Much of this
> strategy is already running code: 31 pytest tests (M1), 68 dbt contracts
> (M2), CI gate with 80% coverage floor. Scope guards applied: drift
> detection = anti-scope; community detection = not in committed graph
> design; load testing = right-sized to latency assertions.

## Already operational (references)
| Area | Where |
|---|---|
| Pyramid rings & API test strategy | backend-design §7 (fake ports / seeded DB / contract) |
| Quality gates, dev/CI parity | Makefile `check` == `.github/workflows/ci.yml`; 80% floor |
| Domain unit testing | Module 1 (invariants as tests) |
| Data contracts, quarantine, reconciliation, known-issues | Module 2 (68 dbt tests, registry with tripwire) |
| ML: leakage battery, reproducibility, eval gates, version pins | ml-system-design §6, §8, §10 |
| XAI: additivity, completeness, version propagation | xai-design §4 |
| Graph: fixture-exact metrics, edge reconciliation | graph-design §6 |
| RAG: golden set, groundedness, SQL safety, citations | rag-design §9 |
| Security: grants-as-architecture, pip-audit, injection defenses | backend §3/§5, rag §8, ci.yml |

## New decisions
1. **API additions (M3 DoD):** schemathesis fuzzing from OpenAPI; contract
   tests for DTO invariants (Scheduled structurally scoreless; versions
   present; TBD enum); auth-path tests. PG service container joins CI in M3
   (loader integration graduates from SQLite to real PG).
2. **Authorization as a test:** connect as fiq_api, attempt silver read,
   assert engine refusal. Same for fiq_analyst. The permission model is
   itself under test.
3. **Power BI (honest):** KPI parity — every kpis.md measure gets a gold
   SQL implementation; .pbix verified against published expected values via
   a documented manual checklist, screenshots archived per release. No
   pretend automation.
4. **E2E = the demo-path test:** empty DB → ingest → dbt build+test →
   score (M5+) → API golden questions → RAG demo questions (M7+). One
   command from existing make targets; run per release and before demos.
5. **Performance:** per-endpoint p95 latency assertions in integration
   tests; batch runtime budget asserted in E2E; query plans reviewed once
   per gold view. Load testing = future (trigger: concurrent users).
6. **Secrets detection:** gitleaks added to pre-commit (small, worth it).

## Test data (4 tiers)
- `tests/fixtures/`: tiny hand-written CSVs for edge cases (TBD rows,
  quarantine bait) — test code, exempt from the data ban.
- Real dataset: local + demo only; never CI.
- Synthetic generator: only if CI needs volume (not yet, deliberately).
- Golden datasets (versioned): RAG QA pairs + labeled sources; expected
  KPI values; API golden responses.

## Folder structure (migrates in M3, when integration tests arrive)
```
tests/
  unit/          # no I/O
  integration/   # needs Postgres; marked, skipped when absent
  e2e/           # demo-path
  fixtures/
transform/tests/ # dbt singular tests (co-located, where dbt wants them)
ml/eval/         # M5: evaluation + leakage battery
```

## Coverage goals
Floor 80% (enforced). Domain/kernel ≥95% (already there). Adapters ~85%.
CLI `__main__` wrappers excluded with comment — meaningful coverage, not
vanity numbers.

## CI gates — final form
- **Per PR (fast, deterministic):** make check (ruff, mypy strict,
  import-linter, pytest+coverage) + dbt parse + fixture integration tests
  (PG service container from M3).
- **Per release (data/cost/judgment):** full dbt tests vs staging; E2E
  demo path; RAG golden set + groundedness; KPI parity; LLM-judge.

## Future extensions (triggers named)
Load testing (concurrent users), drift monitoring (live data feed),
mutation testing (mutmut on kernel/domain), CI-scale synthetic data,
community detection (graph scope ADR).
