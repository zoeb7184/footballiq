# ADR-0002: Clean architecture with a domain-agnostic kernel

- **Status:** Accepted
- **Date:** 2026-07-02
- **Deciders:** Zoeb Ali Khan

## Context
The product is a Decision Intelligence *platform*; football is only the
demonstration domain. The same architecture must later serve manufacturing,
finance, healthcare, logistics, or retail by swapping the domain model and
ingestion adapters — without touching API, ML, BI, or infrastructure layers.

## Decision
We will apply clean architecture (ports & adapters) with a strict inward
dependency rule, plus one platform-specific refinement: a **domain-agnostic
kernel** and **pluggable domain packages**.

Layers and allowed dependencies:

```
api / portal  ──►  application  ──►  domains/*  ──►  kernel
infrastructure ──► application ports (implements them)
```

- `kernel`: generic Entity/ValueObject/Repository/UnitOfWork abstractions,
  domain events, Result types. Stdlib only.
- `domains/football`: pure business logic built on kernel. A new vertical
  (e.g. `domains/manufacturing`) is a sibling package, not a rewrite.
- `application`: use cases; defines ports (interfaces) infrastructure implements.
- `infrastructure`: SQL, storage, LLM, graph adapters. Only layer with I/O libraries.
- `api`: HTTP concerns only.

Import-rule violations fail CI (import-linter, added in Module 1).

## Alternatives considered
| Option | Why rejected |
|--------|--------------|
| Layered MVC (framework-first) | Business logic leaks into controllers/ORM; not portable across domains |
| Microservices from day one | Operational cost with zero benefit at this scale; modular monolith can be split later along these same seams |
| No kernel, football types everywhere | "Reusable platform" becomes a slogan instead of a property of the code |

## Consequences
- (+) Domain swap = new `domains/*` package + new ingestion adapters.
- (+) Domain logic unit-testable without DB, HTTP, or cloud.
- (+) Seams double as future microservice boundaries.
- (−) More indirection than a quick script; discipline required to not bypass ports.
