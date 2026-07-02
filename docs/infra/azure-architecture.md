# Azure Deployment Architecture — Module 9 spec, v1

> Placement of the committed design onto Azure per ADR-0003's swap table.
> No application redesign. Bicep + GitHub Actions implement this in Module 9.
> Cost figures are planning estimates — verify in the Azure Pricing
> Calculator before committing spend.

## 1. Shape
- Compute: **Azure Container Apps** for everything — API, portal, and batch
  jobs (ingest/dbt/score/embed) as ACA Jobs (cron/manual). App Service
  rejected (second paradigm); Functions rejected (jobs are containerized
  CLIs already). Images in ACR Basic.
- Resource groups: rg-fiq-staging, rg-fiq-prod, rg-fiq-shared (ACR, KV).
- Environments: local docker-compose = dev; staging + prod in Azure.
- Region: Germany West Central (data-residency narrative); West Europe
  fallback for SKU availability.

## 2. Data
- **PostgreSQL Flexible Server** — one server per env, all schemas
  (bronze/silver/gold/ai). **pgvector supported natively** → RAG deploys
  unchanged. DB roles (fiq_api, fiq_analyst, pipeline) carry over verbatim.
- Blob Storage: raw landing zone (storage port swap), model artifacts,
  .pbix files.
- Backup: PITR (7→35d); staging LRS, prod geo-redundant.
- DR tiers (honest): portfolio = PITR restore, RTO hours, stated;
  production = geo-backup + restore runbook; replicas/multi-region = future.

## 3. ML (challenge to brief)
**Azure ML rejected for MVP** — replaces our working lightweight registry
(MLOps §10) with a half-configured platform. Mapping: registry table in PG,
artifacts → Blob, batch inference = ACA Job, versioning unchanged.
Azure ML = named extension; trigger: multiple teams/models or compliance
lineage requirements.

## 4. AI layer
pgvector on Flexible Server. Azure OpenAI (or any hosted LLM) behind the
existing LLMClient port — config swap, no code. Embedding job CPU-only
(no GPU anywhere). Cost: token budgets, run-keyed answer cache,
small-model routing.

## 5. Networking (tiered)
- Portfolio/staging: public endpoints + TLS + PG firewall allowlist;
  no VNet (private endpoints ≈ €7/mo each — demo honesty).
- Production: VNet-injected ACA env; private endpoints (PG, KV, Blob);
  PG public access disabled; NSG default-deny; public ingress only for
  API/portal. Front Door/WAF optional.

## 6. Security
Managed identities everywhere; zero connection strings in app config.
Key Vault for true secrets (LLM key, PG admin for migrations). RBAC:
minimal per-identity roles (AcrPull, KV Secrets User, Blob Data R/W per
job). Encryption = platform defaults. Defender: free posture always;
paid plans production-only.

## 7. Monitoring
Log Analytics per env; App Insights via existing OTel exporter swap
(backend §5). Alerts: job failure, API 5xx, /ready failing, PG
CPU/storage, **daily cost anomaly**. One workbook: freshness, latency,
job history, cost.

## 8. CI/CD
GitHub Actions: PR → make check; merge → build → ACR → deploy staging →
smoke (/ready + golden checks) → manual approval → prod. IaC = Bicep
(ADR-0003), spec = this document. Migrations: idempotent init SQL;
dbt run+test as release step (68 contracts = deployment gates).
Rollback: ACA revision pinning + PG PITR; dbt = rerun previous tag.

## 9. Scalability
ACA HTTP autoscale (KEDA); portal scale-to-zero; PG vertical tiers
(honest answer at this volume). AKS = documented path with trigger
(service count/team growth); everything is containers already.

## 10. Cost (planning estimates — verify current prices)
| Tier | Estimate | Notes |
|---|---|---|
| Portfolio (prod only) | ~€25–45/mo | PG B1ms, ACA consumption, ACR Basic, Blob, LA, KV |
| MVP (staging+prod) | ~€50–90/mo | ×~1.7, smallest staging SKUs |
| Production | ~€450–900/mo | PG GP 2–4 vCore + ZR, ACA dedicated, VNet + endpoints, geo-backup, Defender |
+ LLM usage (single-digit €/mo at demo volume with caching).
Biggest lever: PG SKU. Biggest risk: forgotten resources → cost alert.

## 11. Future extensions (out of MVP; triggers named)
AKS (scale/team), Event Hub (only if streaming enters scope — currently
anti-scope), Service Bus (only if commands/async arrive — CQRS has no C),
Cosmos DB (no document/global need), multi-region (needs paying SLA).

## Integration statement
Pure placement: adapter ports (storage/LLM/config), containers, DB-role
security, and OTel hooks were designed for this swap. No application
change required.
