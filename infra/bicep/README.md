# Infrastructure as Code (Bicep)

Azure infrastructure for FootballIQ, implementing `docs/infra/azure-architecture.md`
(portfolio tier). Pure placement of the committed design — no application change.

## What it provisions

`main.bicep` declares, per environment (`staging` / `prod`):

- **Log Analytics** workspace (App Insights via the OTel exporter swap).
- **Container Registry** (Basic) for the API/pipeline images.
- **Key Vault** (RBAC) for true secrets (PG admin, LLM key).
- **Storage account** with `raw` and `artifacts` blob containers.
- **PostgreSQL Flexible Server** (Burstable; B1ms staging / B2s prod) with the
  `footballiq` database, `azure.extensions = VECTOR` (pgvector for the RAG
  store), backups (7d staging / 35d + geo-redundant prod), and an Azure-services
  firewall rule (portfolio tier: public endpoint + TLS, no VNet).
- **Container Apps** environment + the **API** app: system-assigned managed
  identity, AcrPull role assignment, external ingress on 8000, DB URL as a
  secret env var, scale-to-zero on staging.

Batch jobs (ingest / dbt / score / embed) run as ACA Jobs from the same image —
added as the deploy workflow matures; they share this environment and identity.

## Validate

```bash
az bicep build --file infra/bicep/main.bicep      # compile + lint (no Azure needed)
```

## Deploy (staging)

```bash
az group create -n rg-fiq-staging -l germanywestcentral
az deployment group create -g rg-fiq-staging -f infra/bicep/main.bicep \
  --parameters infra/bicep/staging.bicepparam \
  --parameters pgAdminPassword="$PG_ADMIN_PASSWORD" apiImage="$ACR/footballiq-api:$TAG"
```

## Notes / honest limits

- **Portfolio tier only:** public endpoints with TLS + PG firewall allowlist.
  Production hardening (VNet injection, private endpoints, PG public access off,
  managed-identity DB auth instead of a secret URL) is described in the Azure
  architecture doc §5-6 and left as the documented next step.
- Cost is dominated by the PG SKU; see architecture doc §10 for estimates.
  Set a cost alert — forgotten resources are the real risk.
