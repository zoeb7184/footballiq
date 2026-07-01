# FootballIQ Enterprise — Product Requirements Document (PRD)

> Scope authority: `scope.md`. This PRD refines understanding of the MVP;
> it does not expand it. Anything beyond MVP is marked **FUTURE EXTENSION**.

## 1. Product vision
**FootballIQ Enterprise is a decision-intelligence platform that turns
operational event data into auditable, explainable asset decisions —
demonstrated on football, architected for industry.**

Enterprise framing (SAP/Bosch/Siemens register): organizations own portfolios
of expensive assets whose market price lags observable performance. The
platform ingests an asset registry plus operational telemetry, maintains a
governed single source of truth, and answers valuation and outcome-forecast
questions with explainable, board-defensible AI. Auditability, lineage, and
governance are product features, not afterthoughts.

## 2. Business domain in enterprise terms
| Football concept | Enterprise concept |
|---|---|
| Player | Asset / resource with book value |
| Squad / national team | Portfolio / business unit |
| Match | Operational run / production event |
| Match events (goals, cards, VAR) | Operational telemetry / event log |
| Market value | Asset book value / mark-to-market |
| Venue | Facility (capacity, location, elevation) |
| Referee card stats | External compliance/audit factor |
| Tournament stage | Reporting period / campaign phase |

## 3. Target users (enterprise roles)
| Role | Persona equivalent | User story |
|---|---|---|
| Head of Recruitment / Chief Scout | Procurement / talent-acquisition lead | Story 1 (valuation + SHAP shortlist) |
| Director of Football | Portfolio owner / COO | Story 2 (dashboards, budget allocation) |
| Performance Analyst | Business / data analyst | Story 3 (NL questions via RAG) |
| Data & BI Engineer | Internal platform operator | Operates pipelines, warehouse, models |

## 4. Business pain points
1. **Opinion-driven valuation** — market values are consensus numbers that lag
   observable performance; mispricing is invisible until competitors exploit it.
2. **Fragmented data** — registry, events, and stats live in separate sources
   with no lineage; every analysis starts from scratch.
3. **Black-box analytics** — recommendations that cannot be explained cannot be
   defended to a board or audit; explainability is a compliance requirement.
4. **Analyst bottleneck** — ad-hoc questions queue behind the data team;
   decision latency costs opportunities.

## 5. Dataset reality → MVP refinements (no expansion)
Source: World Cup 2026 tournament dataset (11 CSVs: teams, venues, stages,
referees, matches, match events, team stats, lineups, squads/players,
player stats). International tournament — **no transfer ledger exists**.

Refinements:
- **R1** — Dashboard 2 renamed *Talent Valuation Intelligence* (was Transfer
  Market Intelligence). Identical content: value gaps, undervalued players,
  age-value curves. Rationale: tournaments are scouting shop windows.
- **R2** — Minimal graph = **club↔country talent-flow network** from player
  club affiliations (replaces transfer network; same module, same size).
- **R3** — ML feature sets pinned to actual columns:
  - *Player valuation (regression):* age (DOB), position, height, caps,
    international goals, club team, tournament performance stats.
    Label: `market_value`. Metric: RMSLE; % within ±20%.
  - *Match outcome (3-class):* xG, possession, shots (on target), corners,
    team form within tournament, host-nation flag, squad value aggregates.
    Label: match result. Metric: log loss + calibration vs naive baseline.
- Warehouse fit (Module 2 preview, not expansion): facts = matches, events,
  lineups, team stats; dimensions = teams, players, venues, stages, referees.

Everything else in `scope.md` stands unchanged. Both ML labels verified
present in the dataset — the label-availability risk is closed.

## 6. MVP modules (unchanged, roadmap 0–9)
Foundation · Domain core · Data platform · API · Power BI (2 dashboards) ·
ML+XAI (2 models) · Graph (minimal, R2) · RAG (single-turn) · Portal · Ship.
No new modules introduced by this PRD.

## 7. Premium features — FUTURE EXTENSION ONLY
Explicitly out of MVP; each requires an ADR to enter scope (per `scope.md`):
- Multi-competition / club-football data ingestion (incl. real transfer ledgers)
- Injury-risk and availability modelling
- Live match data streaming; in-tournament model updates
- What-if squad/portfolio simulator (scenario planning)
- Pass networks and tactical graphs from event data
- Model monitoring, drift detection, automated retraining
- Multi-tenant SaaS: RBAC, billing, tenant isolation
- Agentic multi-step analytics assistant
- Benchmark & valuation reports as a paid deliverable

## 8. Recruiter positioning (German enterprise market)
One-liner: *"An enterprise decision-intelligence platform with governed data
architecture, explainable ML, and full audit trail — the football domain is
swappable."* Emphasize: Nachvollziehbarkeit (explainability as audit
requirement), data lineage, ADR-driven governance, strict typing/quality
gates, clean architecture with pluggable domains, Azure-ready IaC.
