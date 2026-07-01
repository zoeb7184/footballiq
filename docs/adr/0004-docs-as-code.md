# ADR-0004: Docs-as-code with Mermaid diagrams

- **Status:** Accepted
- **Date:** 2026-07-02
- **Deciders:** Zoeb Ali Khan

## Context
The project standard requires C4, sequence, ER, deployment, and data-flow
diagrams. Diagrams exported from drawing tools rot: they live outside the
repo, are not reviewed, and silently diverge from the code.

## Decision
We will keep all documentation in `docs/` as Markdown with Mermaid diagrams
(diagrams-as-code). Diagrams are versioned, diffable, reviewed in PRs, and
render natively on GitHub. Each module ships a report following
`docs/templates/module-report.md`; each significant decision ships an ADR.

## Alternatives considered
| Option | Why rejected |
|--------|--------------|
| draw.io / Visio exports | Binary/XML blobs; unreviewable diffs; rot silently |
| PlantUML | Needs external renderer; Mermaid renders on GitHub natively |
| Confluence/Notion | Splits truth between repo and wiki |

## Consequences
- (+) Docs evolve in the same PR as the code they describe.
- (+) Recruiters/interviewers see diagrams directly in the GitHub repo.
- (−) Mermaid is less expressive than dedicated tools for very large diagrams
  (mitigation: keep diagrams per-module and small).
