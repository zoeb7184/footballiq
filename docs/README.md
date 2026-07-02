# FootballIQ Documentation Map

> Docs-as-code (ADR-0004): everything versioned with the code it describes.
> Each doc is the single source of truth for its concern. Docs for unbuilt
> modules are deliberately absent — they're deliverables of those modules.

## Start here (by audience)
- **Evaluating the project?** Root [README](../README.md) → [scope](product/scope.md) → module reports below.
- **Understanding decisions?** [ADRs](adr/) — start with [0002 (architecture)](adr/0002-clean-architecture-with-domain-agnostic-kernel.md).
- **Working on the code?** [CONTRIBUTING](../CONTRIBUTING.md) → this map → the design doc for your module.

## Product
- [MVP scope & anti-scope](product/scope.md) — the scope authority; changes require an ADR
- [PRD](product/prd.md) — personas, pain points, enterprise framing

## Architecture & decisions
- [ADRs](adr/) — 0001 process · 0002 clean architecture · 0003 local-first/Azure-ready · 0004 docs-as-code
- [C4 L1 context](architecture/c4-level1-context.md)
- [Backend architecture](api/backend-design.md) — query-only CQRS, DTO contracts, test rings
- [Azure deployment architecture](infra/azure-architecture.md) — Module 9 spec

## Data platform
- [Dataset profiles](data/dataset-profile-batch1.md) ([batch 2](data/dataset-profile-batch2.md)) — measured, not assumed
- [Logical data model](data/logical-data-model.md) — star schema, PRE/POST/DERIVED-ASOF tags, contracts
- [Physical architecture](data/physical-architecture.md) — medallion layers, fact family, DimPlayer

## ML & AI
- [ML system design](ml/ml-system-design.md) — features, labels, models, evaluation, MLOps (Part II)
- [XAI design](ml/xai-design.md) — log-space SHAP, explanation tables, trust rules
- [Graph analytics design](analytics/graph-design.md) — talent-flow network, HHI
- [AI Analyst (RAG) design](ai/rag-design.md) — pgvector, grounded answers, golden-set evaluation

## BI
- [Semantic model & dashboards](bi/semantic-model-design.md)
- [KPI catalog](bi/kpis.md) — single source of truth for BI *and* API

## Quality
- [Testing strategy](testing-strategy.md) — consolidated; most of it is running code

## Module reports (delivery record)
- [00 Foundation](modules/00-foundation.md) · [01 Domain core](modules/01-domain-core.md) · [02 Data platform](modules/02-data-platform.md) · [03 API](modules/03-api.md)
- Template: [module-report](templates/module-report.md)

## Reviews
- [Architecture Review Board — 2026-07-02](reviews/2026-07-02-architecture-review.md)

## Deliberately absent (owned by future modules)
API reference (M3, auto-generated) · model cards (M5) · dashboard guide
(M4) · user guide (M8) · operations runbooks (M9) · CHANGELOG grows per
release at repo root.
