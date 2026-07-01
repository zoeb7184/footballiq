# ADR-0003: Local-first runtime, Azure-ready by construction

- **Status:** Accepted
- **Date:** 2026-07-02
- **Deciders:** Zoeb Ali Khan

## Context
No Azure subscription is available yet. The platform must still demonstrate
cloud architecture skills and be deployable to Azure with minimal change
when a subscription exists.

## Decision
We will run everything locally via docker-compose, choosing each local
component as a drop-in stand-in for its Azure counterpart, and write Bicep
IaC that is lint-validated (`az bicep build`) even though it is not deployed.

| Local (docker-compose) | Azure target | Swap mechanism |
|---|---|---|
| PostgreSQL | Azure Database for PostgreSQL / Azure SQL | connection string |
| Local FS / MinIO | Azure Blob Storage | storage adapter (port) |
| Container images | Azure Container Apps | same images, Bicep |
| .env files | Azure Key Vault | config provider adapter |
| Docker logs | Azure Monitor / App Insights | OpenTelemetry exporter |

All environment access goes through configuration and adapter ports — no
code may read `os.environ` outside the config module.

## Alternatives considered
| Option | Why rejected |
|--------|--------------|
| Wait for Azure subscription | Blocks all progress on a non-technical dependency |
| Azure free tier now | Expiry/cost risk mid-project; local dev loop is faster anyway |
| Cloud-agnostic abstractions for every provider | Over-engineering; we target Azure specifically, adapters give enough portability |

## Consequences
- (+) Zero cloud cost during development; fast inner dev loop.
- (+) Bicep + adapter seams make deployment a config change, not a refactor.
- (−) No live cloud URL for the portfolio until deployment happens.
- (−) Bicep is validated but not exercised against a real subscription (risk of drift).
