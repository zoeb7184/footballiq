# ADR-0001: Record architecture decisions as ADRs

- **Status:** Accepted
- **Date:** 2026-07-02
- **Deciders:** Zoeb Ali Khan

## Context
FootballIQ Enterprise is a long-lived, multi-module platform. Architectural
decisions made early (layering, storage, deployment) constrain everything
built later. Without a written record, the *why* behind decisions is lost,
and future changes re-litigate settled questions.

## Decision
We will record every architecturally significant decision as a numbered ADR
in `docs/adr/`, using `template.md`. "Architecturally significant" means the
decision had real alternatives and affects structure, dependencies, data,
or operations. Routine choices do not get ADRs — signal over ceremony.
ADRs are immutable once accepted; reversals create a new ADR that supersedes
the old one.

## Alternatives considered
| Option | Why rejected |
|--------|--------------|
| Wiki / external docs | Drifts from code; not reviewed in PRs |
| No records | Decisions re-argued repeatedly; onboarding cost grows |

## Consequences
- (+) Every design choice is auditable and interview-defensible.
- (+) New contributors read `docs/adr/` and understand the system's reasoning.
- (−) Small writing overhead per significant decision.
