# C4 Level 1 — System Context

FootballIQ Enterprise as a black box: who uses it, what it talks to.

```mermaid
C4Context
    title FootballIQ Enterprise — System Context

    Person(analyst, "Analyst / Scout", "Explores dashboards, asks natural-language questions")
    Person(exec, "Decision Maker", "Consumes KPIs and AI recommendations")
    Person(engineer, "Data Engineer", "Operates pipelines and warehouse")

    System(fiq, "FootballIQ Enterprise", "AI Decision Intelligence Platform: warehouse, API, ML+XAI, graph analytics, RAG assistant")

    System_Ext(sources, "External Data Sources", "Kaggle datasets; later StatsBomb events")
    System_Ext(pbi, "Power BI", "Enterprise BI dashboards over the gold layer")
    System_Ext(llm, "LLM Provider", "Hosted LLM API for RAG assistant")

    Rel(analyst, fiq, "Uses portal / API")
    Rel(exec, pbi, "Views dashboards")
    Rel(engineer, fiq, "Runs / monitors pipelines")
    Rel(fiq, sources, "Ingests raw data (batch)")
    Rel(pbi, fiq, "Queries gold layer (SQL)")
    Rel(fiq, llm, "Grounded prompts (RAG)")
```

## Notes
- Football is the demonstration domain. Replacing `sources` and
  `domains/football` retargets the platform to another industry (ADR-0002).
- Level 2 (containers) will be added in Module 2 when the runtime
  components (API, warehouse, pipelines, portal) exist.
