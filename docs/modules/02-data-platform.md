# Module 2 — Data Platform

## 1. Requirements
Implement the physical data architecture v2: bronze/silver/gold medallion,
idempotent ingestion, data contracts as executable checks, star schema.

## 2. Architecture
Python owns ingestion (bronze); dbt owns transformation (silver→gold).
Layers = Postgres schemas with per-layer governance; API role grant-locked
to gold at container init. See `docs/data/physical-architecture.md`.

## 3. Design rationale
- **Bronze append-only, all TEXT:** no interpretation at landing; every load
  stamped (load_id, sha256, timestamp); unchanged file = recorded no-op.
- **Latest-load pattern:** silver reads only the newest load per source —
  idempotency at the read side, history preserved at the write side.
- **Quarantine as a model:** contract violations preserved with reasons;
  quarantine-empty is a WARN (data finding), broken grain is an ERROR.
- **Reserved members (−1 Unknown, −2 TBD)** unioned into dims; fact_match is
  the single point where source nulls become members.
- **Surrogate = natural key at MVP** (single source, deterministic);
  hash-key strategy documented as the multi-source upgrade path.
- **matches_detailed bronze-only**, used by a reconciliation test.

## 4. Implementation
Slice 1: docker-compose Postgres + schema/role init; config module (sole
env reader); 11-source manifest; BronzeLoader (engine-agnostic, registry,
sha256 idempotency). Slice 2: dbt scaffold (verbatim-schema macro,
latest_load macro), 6 silver models + quarantine. Slice 3: 4 more silver
models (dead columns dropped, GK nulls structural), 6 dims + dim_date,
4 facts + snapshot, reconciliation tests.

## 5. Testing
**Validated on host (2026-07-02):** 7,428 rows ingested (re-run = 11 no-ops);
22 dbt models built; **67 PASS / 1 WARN of 68 data tests**. Goal-sum
reconciliation, matches_detailed reconciliation, grain tests, all FK
relationships: PASS. The WARN (snapshot vs event goals, 9 players) is a
definitional finding under investigation — warn-severity behaved as designed.
Python side: 31 pytest tests incl. loader idempotency on SQLite.

## 6. Future improvements
- Coverage-percentage metric logged per load (currently a static declaration)
- Incremental dbt materializations if data volume ever warrants it
- dbt docs site generation (free lineage visualization) in CI

---

## Portfolio annex
- **Skills demonstrated:** medallion architecture, dbt engineering, data
  contracts as tests, idempotent ELT, dimensional modeling, reconciliation
  testing, Docker, database security roles.
- **Interview questions prepared:** "Design an idempotent ingestion
  pipeline." "How do you handle bad rows?" "Where do nulls become dimension
  members?" "Warn vs fail in data tests?" "Star schema from scratch."
- **Enterprise concepts applied:** single source of truth, declared
  coverage, quarantine-not-drop, grant-enforced layer access, lineage
  stamping.
- **Resume bullet:** "Built a medallion warehouse (Postgres + dbt) with
  idempotent hash-stamped ingestion, executable data contracts (68 tests),
  quarantine-with-reason handling, and a reconciliation suite that verifies
  event-level facts against recorded aggregates."
- **LinkedIn:** "Module 2 shipped: the data platform. 11 CSVs → bronze →
  silver → gold star schema, 68 executable data contracts. Favorite moment:
  the pipeline's first WARN was a real definitional discrepancy the
  reconciliation tests were designed to catch."
