# FootballIQ Operations Runbook

Operational procedures for running, deploying, and recovering the platform.
Scope: local demo + Azure portfolio/prod tiers (docs/infra/azure-architecture.md).

## 1. Run locally (one command)

```bash
pip install -e ".[dev,rag,portal]"   # tooling + ML + RAG + portal
make demo                            # warehouse -> pipeline -> model -> graph -> RAG index -> smoke
make api                             # http://localhost:8000/docs
make portal                          # http://localhost:8501
make bi-up                           # http://localhost:3000
```

`make demo` fails loudly if any layer is empty (scripts/demo_smoke.py). Data CSVs
must be in `data/raw/` (never committed).

## 2. Deploy to Azure

- **PR:** CI runs `make check`; `deploy.yml` validates Bicep (`az bicep build`).
- **Merge to main:** build image -> ACR -> deploy **staging** -> smoke (`/ready`
  == 200) -> **manual approval** (production Environment) -> deploy **prod**.
- **First-time setup:** create resource groups (`rg-fiq-staging`, `rg-fiq-prod`,
  `rg-fiq-shared`), an OIDC app registration with federated credentials, and set
  repo vars (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`,
  `ACR_NAME`) + secret (`PG_ADMIN_PASSWORD`).
- **Migrations:** the init SQL (schemas, roles, pgvector, ai.query_log) is
  idempotent; run `make ai-up` equivalent against the server. dbt `run` + `test`
  (68 contracts) is a release gate — a broken contract blocks promotion.

## 3. Rollback

- **App:** pin the previous ACA revision
  (`az containerapp revision set-mode`/`activate`) — instant, no rebuild.
- **Data (dbt):** re-run the previous git tag's models
  (`git checkout <tag> && make transform`).
- **Database:** PostgreSQL PITR restore (§4). Use only for data corruption, not
  app bugs (prefer revision pinning).

## 4. Backup & restore

- **Backups:** Flexible Server automated backups — 7 days (staging), 35 days +
  geo-redundant (prod). No manual action for routine PITR.
- **Restore (RTO: hours, stated honestly):**
  `az postgres flexible-server restore --restore-time <ISO> --source-server <src>
  --name <new>`, repoint `FIQ_DATABASE_URL` (Key Vault secret + ACA revision),
  verify with `/ready` and `scripts/demo_smoke.py` against the restored server.
- Model artifacts live in Blob (`artifacts` container) and are re-derivable via
  `make train` from a pinned feature_version if lost.

## 5. Incident response

| Symptom | First checks | Action |
|---|---|---|
| API 5xx spike | Log Analytics `ContainerAppConsoleLogs`; correlation_id in problem+json | pin previous revision; check PG health |
| `/ready` failing | which check fails (fact_match / prediction empty) | rerun the missing batch job (`pipeline`/`score`) |
| RAG answers ungrounded | `ai.query_log` (grounded=false rows) | re-`index`; verify model/feature versions pinned |
| PG CPU/storage alert | server metrics | scale SKU up one tier (vertical); investigate query |
| Cost anomaly alert | Cost Management by resource | find forgotten resources; the PG SKU is the main lever |

Every analyst answer is reconstructible from `ai.query_log` (question, route,
sources, response hash, versions).

## 6. Secrets & security

- True secrets (PG admin, LLM API key) live in **Key Vault**; the API reads them
  via managed identity — no connection strings in app config.
- Rotate PG admin: update the KV secret, restart the ACA revision.
- DB roles enforce least privilege: `fiq_api` and `fiq_analyst` are SELECT-only
  on gold (+ ai for the analyst); nothing reaches bronze/silver.

## 7. Routine checks

- Daily: cost anomaly alert; job-failure alerts (ingest/dbt/score/embed).
- Per release: dbt contracts green; golden RAG questions grounded; `/ready` 200.
- Freshness/latency/job-history/cost on the single Log Analytics workbook.
