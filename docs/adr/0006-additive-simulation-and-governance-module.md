# ADR-0006: Add match simulation and model-governance endpoints (Module 10)

- **Status:** Accepted
- **Date:** 2026-07-18
- **Deciders:** Zoeb Ali

## Context
The production web frontend (frontend blueprint) needs two capabilities the
v1.0.0 API does not expose: a match simulator and a model-performance view.
scope.md requires an ADR before adding scope. The platform's trust rule —
no invented numbers — must hold: the original wish list also included live
predictions and event intelligence, which have no honest data source in the
warehouse and are therefore rejected, not approximated.

## Decision
We will add one additive vertical slice (M10) with two read-only-adjacent
endpoints: `POST /v1/simulations/match`, a seeded Monte Carlo over warehouse
Elo ratings (Elo win expectancy → Poisson goal rates split by expectancy;
total-goal rate observed from completed matches, falling back to the sourced
FIFA WC 2022 average of 172/64; Wilson 95% intervals on every probability;
assumptions returned in-band), and `GET /v1/models/performance`, serving
training-time registry entries (params, seed, git commit, CV metrics vs
baselines) plus global mean |SHAP| aggregated from stored explanation rows.
Nothing existing is modified beyond composition-root wiring and an opt-in
CORS setting. Qualification probability is **deferred**: honest group/bracket
odds require FIFA tie-break inputs (disciplinary points, drawing of lots) the
warehouse does not hold — computing them would violate the no-invention rule.

## Alternatives considered
| Option | Why rejected |
|--------|--------------|
| Frontend-only simulation (client-side math) | Duplicates model logic outside the tested core; unreproducible; contradicts API-as-source-of-truth |
| Full xG/Poisson regression model (Dixon-Coles) | Needs match-level covariates and fitting infrastructure; out of proportion for an explicitly-labeled baseline |
| Qualification probabilities now | Tie-break data not in warehouse; results would be fabricated precision |
| Serving artifact meta.json for performance | Registry table already holds the same lineage with status/promotion history; DB is the single source |

## Consequences
Positive: the two highest-impact frontend pages get real endpoints; the
simulator is deterministic per seed (CI-checkable) and self-describing.
Negative: the goal-split assumption (goal share ~ Elo expectancy) is a
simplification and is labeled as such in every response; simulation runs at
request time (bounded at 10,000 runs, pure stdlib, ~ms-scale) — a deliberate,
bounded exception to prediction-as-data. Risk: consumers may quote the
probabilities without the intervals; mitigated by shipping CIs and assumptions
in the same payload rather than in documentation only.
