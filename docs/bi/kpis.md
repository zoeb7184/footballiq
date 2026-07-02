# KPI Catalog — single source of truth

> Every KPI is defined once here. Power BI measures and API aggregations
> implement these definitions verbatim; divergence is a defect.
> DAX/SQL aggregate gold columns only — no ML or contract logic recomputation.

| KPI | Definition | Grain/context | Source columns |
|---|---|---|---|
| Win Rate | wins ÷ completed matches | team, filter-context aware | fact_match |
| Points | 3·W + 1·D (group stage only) | team | fact_match |
| Tournament Progression | max stage reached (dim_stage order) | team | fact_match, dim_stage |
| xG Differential | Σ(xG for) − Σ(xG against) | team | fact_match |
| Form (last N) | rolling points over last N completed matches | team, N=3 default | fact_match, dim_date |
| Squad Value | Σ market_value_eur | team | dim_player |
| Median Player Value | median market_value_eur | team/position | dim_player |
| Player Value Gap | predicted_value_eur − market_value_eur | player; Σ/avg in context | prediction_player_valuation |
| Team Strength Index | mean(Elo percentile, squad-value percentile) | team | dim_team, dim_player |
| Attack Output /90 | (goals+assists) ÷ minutes × 90, minutes floor 90 | player vs positional peers | fact_match_event, fact_player_match |
| Supply Concentration (HHI) | Σ (club share of squad)² | nation | graph_metrics_nation |
| Data Freshness | latest scored_at / load run | platform | run metadata view |

Notes:
- "Expected value contribution" (player xG share) is not buildable from this
  dataset (no player-level xG) — Attack Output /90 is the honest substitute.
- Knockout matches award no draw points; Points measure applies group rules
  to group stage only.
