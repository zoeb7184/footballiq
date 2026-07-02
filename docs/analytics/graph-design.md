# Graph Analytics Design — v1 (minimal, per scope R2)

> Constraints honored: prediction-as-data, batch-only, read-only API.
> **Feasibility (measured):** match_events contains only Goal/Assist/Card/VAR
> — pass networks are data-infeasible, independent of anti-scope.
> Rejected as too sparse / serving no user story: lineup co-appearance,
> assist→goal dyads (152 edges). Future extensions only.

## 1. Graph model (one graph)
Bipartite **club ↔ national team talent-flow** network.
- Nodes: ~450 clubs (normalized club_team string = node key; no dim_club) +
  48 nations (dim_team).
- Edges: club supplies player(s) to nation; weight = player count;
  value-weighted variant = Σ market_value_eur.
- Source: squads_and_players via dim_player (warehouse reuse only).
- One-mode projections (club–club, nation–nation) derivable on demand.

## 2. Metrics (deterministic, batch)
| Metric | Football | Enterprise reading |
|---|---|---|
| Weighted degree (club) | top talent suppliers | supplier importance |
| Value exported (club) | Σ value supplied | supplier contract volume |
| Supply concentration HHI (nation) | squad dependence on few clubs | **supplier concentration risk** |
| Cross-confederation edges | talent globalization | cross-regional sourcing exposure |

## 3. Physical
Batch job after warehouse load → gold tables:
- graph_edge_talent_flow (club, team_sk, player_count, total_value) —
  doubles as visualization data
- graph_metrics_club, graph_metrics_nation
Versioned by graph_version + load run; deterministic (no seeds).
**Engine: NetworkX in batch. No graph DB** (~500 nodes / ≤1,248 edges);
Neo4j = future extension.

## 4. Consumers
- API: /v1/graph/talent-flow (edge list); /v1/graph/clubs?sort=
  value_exported; /v1/graph/nations/{id}/supply-concentration.
- Power BI: metrics tables only (ranked bars, concentration matrix) —
  PBI is not a network-viz tool. Network diagram lives in Streamlit via API.
- Dashboard budget unchanged: visuals join existing 2 dashboards' pages.

## 5. ML boundary
Graph metrics are analytics products, **not ML features** in MVP.
Club centrality as valuation feature = future extension (major
feature_version bump when adopted).

## 6. Testing
Fixture graph with hand-computed centralities/HHI (exact assertions);
Σ edge player_counts = 1,248 reconciliation; projection symmetry.
