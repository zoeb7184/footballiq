# BI Semantic Model & Dashboard Design — v1 (Module 4 spec)

> **Implementation note (ADR-0005):** implemented in **Metabase**, not
> Power BI (macOS constraint). This design is tool-portable and stays
> authoritative: same star, dashboards, and KPI catalog. Role-playing
> dim_team uses the alias-view fallback (§1); measures become versioned
> SQL in `docs/bi/queries/`.

> Scope ruling: scope.md caps MVP at **2 dashboards**; monitoring dashboards
> are anti-scope. Everything beyond the two below = FUTURE EXTENSION (ADR
> required). Reports use pages, not extra dashboards.

## 1. Semantic model (import mode, gold only)
- **Facts:** fact_match, fact_match_team_stats (partial coverage declared),
  player_tournament_snapshot (BI-only home), prediction_player_valuation,
  prediction_match_outcome, explanation_player_valuation.
- **Dims:** dim_player, dim_team, dim_venue, dim_stage, dim_referee, dim_date.
- **Versioning:** model reads current-production views (vw_prediction_*
  pinned in gold). Version arbitration in warehouse, never DAX.
- **Relationships:** fact←dim only; single-direction; 1:N; surrogate keys
  (natural keys hidden). **No bidirectional filters.**
- **Role-playing dim_team:** home relationship active, away inactive
  (per-measure activation); alias views = fallback.
- **Bridges: none** (grains meet dims via conformed keys; explanation table
  is player-grain long format → direct relationship).
- **Status:** filterable column; analytics pages default Completed; schedule
  page shows Scheduled; TBD renders via reserved member.

## 2. Dashboards (2, final)
**D1 Executive Squad Overview** (Director of Football)
- P1 Tournament Pulse: KPI cards (squad value, points, xG diff, stage);
  value-vs-points quadrant (primary business question visual); rankings;
  progression funnel.
- P2 Team Performance: rolling form, xG vs goals, host/neutral split,
  stage comparison.
- Decisions: budget allocation; over/under-delivery per €.

**D2 Talent Valuation Intelligence** (Chief Scout / analyst)
- P1 Scout Shortlist: value-gap table (predicted vs market), age-value
  scatter, undervalued top-N, global importance margin visual.
- P2 Player Explanation (drill-through): XAI page — see §3.
- P3 Talent Flow: supplier-club bars (value exported), nation HHI bars
  (graph design §4).
- Decisions: shortlist; sourcing concentration risk.

Data freshness = footer card on both (scored_at + load run via gold view).

**FUTURE EXTENSIONS (named only):** coach/tactical, operations, AI model
monitoring (anti-scope; premature with one static dataset), API usage.
**Player similarity: not in any committed design — future extension.**

## 3. XAI page
Drill-through from any player visual → context-filtered explanation page:
- Tornado bar: multiplicative_factor sorted by |shap_log| ("×1.6", "−45%").
- Baseline→prediction bridge: waterfall over shap_log (exact in log space),
  € only at endpoints; factor labels.
- Attribute card with feature_value tooltips.
- Trust footer: model_version, scored_at, ±20% note, attributional caption
  (XAI design §6).
DAX binds stored columns; no SHAP math in BI.

## 4. DAX measure catalog (requirements → docs/bi/kpis.md)
Rule: DAX aggregates gold; never recomputes ML/contract logic.
Win Rate; Points; Tournament Progression (dim_stage order); xG Differential;
Form (rolling last-N via dim_date); Squad/Median Value; Player Value Gap
(Σ predicted − market, stored columns); Team Strength Index (documented
composite: Elo percentile + squad-value percentile); host-advantage splits.
"Expected value contribution" per player not honestly buildable (no player
xG) → replaced by goals+assists/90 vs positional peers, limitation noted.

## 5. Filters
Global: stage, confederation, team, status (page defaults). D2 adds:
position, age band, value band, club. Drill: Tournament→Stage→Match→Player.
Season slicer = future extension (single tournament; no fake filters).

## 6. Sources (strict)
All visuals → gold semantic model; predictions → vw_prediction_*;
explanations → explanation tables; graph → graph_metrics; freshness →
run-metadata view. Raw CSVs appear nowhere.
