# ADR-0005: Metabase replaces Power BI as the BI tool

- **Status:** Accepted
- **Date:** 2026-07-02
- **Deciders:** Zoeb Ali Khan

## Context
scope.md and the BI design specify Power BI. Power BI Desktop — where all
modeling happens — is Windows-only; development is on macOS, and the
developer is a student (no Windows license/VM budget). Module 4 is blocked
on tooling, not design.

## Decision
We will implement the two MVP dashboards in **Metabase** (open-source,
self-hosted), running as a container in the existing docker-compose stack
and connecting to the warehouse **as the `fiq_api` role** — so BI access is
grant-enforced gold-only, identical to the API's guarantee.

The BI *design* is tool-portable and stays authoritative: same star schema,
same two dashboards and pages, same KPI catalog. KPI definitions are
implemented as **versioned SQL** (`docs/bi/queries/`) used by Metabase
questions — which also realizes the testing strategy's KPI-parity
mechanism (one SQL truth per KPI).

Role-playing dim_team uses the alias-view fallback already named in the
semantic model design (Metabase has no per-measure relationship
activation).

## Alternatives considered
| Option | Why rejected |
|--------|--------------|
| Power BI Desktop (Windows VM) | License + VM cost/complexity for a student; blocks demo-in-compose |
| Power BI Service (browser) | Modeling still requires Desktop |
| Apache Superset | Heavier setup, steeper curve; overkill for 2 dashboards |
| Lightdash | Attractive dbt coupling, but younger/fiddlier |
| Tableau Public | Cannot privately connect to a database |

## Consequences
- (+) BI joins the one-command compose demo (better than .pbix screenshots).
- (+) Grant-enforced gold-only BI via fiq_api — a stronger security story.
- (+) KPI SQL versioned in the repo (parity mechanism realized).
- (−) "Power BI" becomes design-doc knowledge rather than hands-on artifact
  on the CV; the semantic-model doc is retained as evidence and remains
  implementable in PBI unchanged if a Windows environment appears.
- Azure doc's PBI-specific items (.pbix in Blob, embedding) become
  future-extension notes; Metabase deploys as one more ACA container.
