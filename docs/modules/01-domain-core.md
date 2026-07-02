# Module 1 — Domain Core

## 1. Requirements
Implement the kernel abstractions and football entities specified by the
logical data model — invariants as code, not documentation.

## 2. Architecture
Kernel (stdlib-only) + pluggable football domain per ADR-0002. Layer rules
now mechanically enforced via import-linter contract in pyproject.

## 3. Design rationale
- **Exceptions vs Result split:** invariant violations raise
  `InvariantViolation` (bugs/bad data — fail loudly); expected operational
  failures use `Result` at boundaries. One mechanism per failure class.
- **Aggregates reference by ID** (Match holds TeamId, not Team) — DDD
  boundaries; mirrors warehouse FK semantics; keeps serialization trivial.
- **TBD is a type** (`TeamId | TbdOpponent`) — the type checker forces every
  consumer to handle the undetermined-opponent state; no nulls to interpret.
- **Typed IDs (NewType):** PlayerId/TeamId mix-ups become type errors.
- **Forward-only lifecycle:** `complete()` is the only transition; a second
  call raises. Implements the accumulating-status fact contract.
- **Knockout no-draw** enforced at `complete()` — stage-conditional outcome
  space from the logical model, §4.

## 4. Implementation
kernel/: errors, result (Ok/Err), entity (identity equality), value_object
marker, ports (Repository/UnitOfWork protocols).
domains/football/: ids, enums, values (Score, XgPair, TbdOpponent),
player (with `age_at` fixed-reference age per ML design), team/venue/stage/
referee, match (lifecycle aggregate).

## 5. Testing
19 invariant paths: kernel identity/result semantics; match lifecycle
(structural nulls, forward-only, knockout draw ban, TBD resolve→complete,
self-play ban); player/team/venue invariants; birthday-boundary age cases.
Sandbox verification: full functional smoke (PyPI unavailable in-session);
authoritative gate = `make check` on host (ruff, mypy strict, import-linter,
pytest).

## 6. Future improvements
- Domain events (kernel has no event plumbing yet — added when a consumer exists)
- MatchEvent/Lineup entities (Module 2 decides silver-only vs domain)
- Hypothesis property-based tests for Score/age edge cases

---

## Portfolio annex
- **Skills demonstrated:** DDD tactical patterns (entities, VOs, aggregates),
  type-driven design, invariant enforcement, protocol-based ports,
  architecture-as-code (import-linter).
- **Interview questions prepared:** "Entity vs value object?" "How do you
  make illegal states unrepresentable?" "Exceptions vs Result types?"
  "What is an aggregate boundary and why reference by ID?"
- **Enterprise concepts applied:** ubiquitous language from the data
  contracts; fail-fast invariants; dependency rule enforced mechanically.
- **Resume bullet:** "Implemented a type-driven domain core (DDD) where data
  contract rules — lifecycle transitions, undetermined-entity states,
  stage-conditional outcomes — are compile-time and constructor-enforced
  invariants, with architecture rules enforced by import-linter in CI."
- **LinkedIn:** "FootballIQ Module 1 shipped: the domain layer. Favorite
  detail — a TBD opponent is a *type*, not a null. The compiler now refuses
  code that forgets undetermined knockout slots exist."
