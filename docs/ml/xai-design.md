# XAI System Design — v1

> Respects: prediction-as-data (no runtime inference), SHAP precomputed at
> batch scoring, versioned feature store, read-only API over gold, Power BI
> first-class. Scope per scope.md: full SHAP for valuation only; outcome
> model gets global importance only.

## 1. Taxonomy
| | Valuation | Outcome |
|---|---|---|
| Local | Full SHAP (product feature, story 1) | ❌ MVP excluded |
| Global | mean-\|SHAP\| importance | standardized per-class coefficients (its only XAI deliverable) |

**Future extensions only:** counterfactuals, PDP/ICE, per-match outcome
explanations, uncertainty intervals (new model — excluded), LLM narrative
generation (Module 7 may render stored SHAP; never computes attributions).

## 2. Log-space handling (core decision)
Valuation predicts log(value) → SHAP is additive in log space; additive
€ decompositions are mathematically wrong.
- **Canonical:** raw log-space SHAP φᵢ (exact: base + Σφᵢ = log(pred)).
- **Display:** multiplicative factors exp(φᵢ) — "caps: ×1.6 (+60%)";
  product of factors × baseline (geometric-mean value) = prediction exactly.
- Outcome model importance from standardized multinomial-logistic
  coefficients; schema is method-agnostic if GBT replaces it.

## 3. Computation & storage
- SHAP computed in the same batch scoring run as predictions; one atomic
  load — explanation cannot exist without its matching prediction.
- TreeSHAP, all players × all features (~25K rows): store everything.
- **gold.explanation_player_valuation** (player × model_version × feature):
  feature_name, feature_value (as model saw it), shap_log, multiplicative
  _factor, rank, feature_version, scored_at. **Long format — required by
  Power BI visuals.**
- **gold.explanation_global** (model × model_version × feature):
  importance, rank, direction.
- Baseline (expected value) stored per model_version.
- Prediction table keeps denormalized top-k payload for one-call API reads;
  long table is source of truth.

## 4. Consistency & governance
- **Write-time additivity check:** base + Σ shap_log = log(pred) within
  tolerance; failing rows fail the load (invariant, not hope).
- Pinned to model_version + feature_version (join keys; mismatch = load
  failure). Immutable per scoring run; superseded on re-score, never edited.

## 5. Consumers
- **API:** top-k inline in valuation response;
  /v1/players/{id}/valuation/explanation (full breakdown + baseline);
  /v1/models/{task}/importance. All responses versioned.
- **Power BI:** explanation table ↔ dim_player; Dashboard 2 drill-through:
  value-gap table → player explanation page (multiplicative-factor tornado
  + baseline→prediction bridge); global importance bar.
- **Streamlit:** player detail via API only (proves API contract
  sufficiency; no direct DB reads).

## 6. Trust rules
Every rendered explanation shows model_version + scored_at. Attributional
language only ("model associates…"), never causal; standing footnote: SHAP
explains the model, not the market. ±20% accuracy figure displayed beside
valuations.
