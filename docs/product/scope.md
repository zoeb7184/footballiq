# FootballIQ Enterprise — MVP Scope (authoritative)

> Scope control document. Features outside this document require an ADR to
> enter scope. Tested against in every module review.

## Primary business question
**"Which players should we buy or sell, and at what price, to maximize squad
performance per euro spent?"**
Domain-agnostic form: resource allocation under budget constraint
(machines in manufacturing, assets in finance, fleet in logistics).

## MVP definition
A dockerized analytics platform that ingests one Kaggle football dataset into
a medallion warehouse, serves player-valuation and match-outcome predictions
with explanations via API and portal, and ships two Power BI dashboards —
one business question answered end-to-end, production-grade per layer.

## User stories (max 3)
1. **Scout** — search/filter players; see predicted market value with SHAP
   explanation; build a defensible shortlist.
2. **Director of Football** — view squad value vs. performance dashboards;
   allocate transfer budget.
3. **Analyst** — ask natural-language questions grounded in warehouse data
   (single-turn RAG).

## ML use cases (max 2)
| | Player Market Value | Match Outcome |
|---|---|---|
| Type | Regression | 3-class classification |
| Input | Age, position, performance stats, contract features | Team form, squad aggregates, home advantage |
| Output | Estimated value (€) | Calibrated P(W/D/L) |
| Business value | Detect mispriced players | Validate squad decisions |
| Metric | RMSLE; % within ±20% | Log loss; calibration vs naive baseline |
| XAI | SHAP (required) | Global feature importance only |

## Power BI dashboards (max 2)
1. **Executive Squad Overview** — squad value, KPIs, value-vs-performance quadrant.
2. **Transfer Market Intelligence** — model-vs-market value gaps, undervalued
   players, age-value curves.

## Anti-scope (excluded from MVP)
- Live/real-time data, streaming (Kafka), StatsBomb event data, pass networks
- Injury prediction, video/tracking data, betting features, fantasy features
- Multi-tenancy, billing, RBAC admin UI (API-key auth only)
- Auto-retraining, AutoML, model-monitoring dashboards
- Kubernetes, multi-cloud (docker-compose local; Azure-targeted IaC only)
- Custom React frontend, mobile apps, i18n
- Agent frameworks beyond single-turn RAG

Note: a minimal transfer-network graph module stays in scope (reuses
warehouse data); event-data pass networks do not.

## Portfolio completion criteria
- **Architecture:** all layers present; the valuation vertical slice
  (ingest → warehouse → model → API → portal → dashboard) production-quality.
- **Features:** 2 models (one with SHAP), 2 dashboards (.pbix + screenshots),
  documented API, RAG assistant answering 5 demo questions reliably.
- **Deployment:** `docker compose up` one-command demo; green CI badge;
  lint-valid Bicep.
- **Documentation:** README with diagrams, ~10 ADRs, module reports,
  auto-generated API docs, 3-minute demo script.
