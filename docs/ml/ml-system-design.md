# ML System Design — v1.1

> Phase 5 design. No code/training — implementation in Module 5.
> Governance basis: availability tags (logical model §3), feature layer
> (physical architecture §4), profiles batch 1–2.
> v1.1 adds Part II (pipelines, serving, MLOps). Part I is settled design —
> extended, never rewritten.

## 1. Problem decomposition
| | Player Valuation | Match Outcome |
|---|---|---|
| Type | Cross-sectional regression | 3-class classification, stage-conditional (no draws in knockout) |
| Label | log1p(market_value_eur) | W/D/L from final scores, Completed only |
| Business | Value gap = predicted − listed → mispricing shortlist (story 1) | Squad validation (story 2 support) |

**Not ML tasks:** xG modeling (consumed input); similarity/clustering;
injury prediction (anti-scope); lineup optimization; RAG (retrieval, no
training); graph centrality (deterministic); temporal value forecasting
(single label snapshot — no series).

## 2. Feature design
### A. Valuation (cross-sectional; no as-of cutoffs needed within model)
- **Registry attributes:** age at tournament start (fixed reference date),
  position, height, caps, international goals.
- **Tournament performance:** goals, assists, starts, minutes, cards from
  fact_match_event + fact_player_match; per-90 with minutes floor —
  low-minute players shrunk toward position means and flagged.
- **Context:** team Elo, confederation, club.
- **Rules:** (1) **no label-derived features** — any aggregate touching
  market_value_eur banned in this model. (2) club (450 cats): out-of-fold
  target encoding or frequency encoding, chosen by ablation — never naive
  target encoding. (3) player_tournament_snapshot never a feature source.

### B. Outcome (PRE + DERIVED-ASOF only)
- **PRE:** Elo, FIFA rank, stage, venue elevation, host flag
  (home advantage = is_host × own-country venue — most matches are neutral),
  squad aggregates from dim_player (median value/age/caps — legal here).
- **DERIVED-ASOF:** points/goals/xG for-against to date, rest days;
  cutoff = kickoff; only strictly earlier completed matches.
- **Aggregation: difference features** (home − away) — anti-symmetry,
  halves dimensionality; critical at N=76.
- **Team-stats features (66/76 coverage): restrict, don't impute** —
  ablation only, not main feature set.

## 3. Feature store
- gold.feature_player_valuation (player × feature_version).
- gold.feature_match_prematch (match × feature_version, cutoff_ts).
- One builder codepath for training (historical cutoffs) and inference
  (scheduled matches) — skew designed out.
- **Registry:** name, dtype, availability tag, source facts, formula,
  version introduced; CI rejects unregistered features.
- **Versioning:** semantic; additive = minor, formula change = major;
  models pin exact feature_version.

## 4. Label engineering
- Valuation: log1p; €200M tail retained. Never feature/ingredient in own
  model; legal as PRE squad aggregate in outcome model.
- Outcome: from final scores; knockout = final result (ET/pens embedded —
  documented assumption); TBD matches excluded.
- Timing: labels join only to features with earlier cutoff.

## 5. Model strategy
| | Baseline (mandatory, reported) | Production | XAI |
|---|---|---|---|
| Valuation | position median; linear on log | gradient-boosted trees | Full SHAP (local + global); log→€ back-transform documented |
| Outcome | majority class; Elo-difference logistic | regularized multinomial logistic; GBT only if honestly better | global importance only |

- Calibration: temperature scaling on out-of-fold predictions (isotonic
  overfits at N=76); verified by calibration curve.
- **Honesty criterion:** beating Elo baseline at N=76 is unlikely; success =
  matching baseline log loss with calibrated, explainable probabilities,
  reported as such.

## 6. Evaluation framework
- **Valuation:** grouped 5-fold CV by national team (random folds leak team
  context). RMSLE, median APE, % within ±20%, per-position breakdown;
  always vs both baselines.
- **Outcome:** expanding-window backtest along tournament timeline (train
  < day t, predict day t) — mirrors live usage. Log loss, Brier,
  calibration vs uniform + Elo.
- **Leakage battery (CI):** recompute-at-cutoff equality; registry tag audit
  on every model input; shuffled-label test (performance must collapse to
  chance); valuation label-lineage assertion.

---

# Part II — Pipelines, Serving, MLOps (v1.1)

## 7. Pipeline architecture
**Training (batch, deterministic):** gold facts/dims → versioned feature
builder → materialized feature tables → per-model training job →
**evaluation gate** (baseline comparison + leakage battery; fail = no
registration) → registry entry. Orchestration = CLI entrypoints via make
targets. No workflow orchestrator at this scale (deliberate).

**Inference (batch "tournament mode"):** each data refresh → rebuild
features → score all players + predictable scheduled matches → write
prediction tables. **SHAP computed at batch time, stored with prediction.**
**Prediction-as-data:** the API never runs a model — it reads
gold.prediction_* tables. Auditable, lookup-latency, no training/serving
drift. **No real-time inference in MVP** (documented assumption; request
path is read-only).

Flow: ingest → warehouse → feature build → train (occasional) / score
(every refresh) → prediction tables → API + Power BI (same gold).

## 8. Feature store integration (delta)
- Models consume only materialized gold.feature_* rows matching pinned
  feature_version; trainer and scorer refuse mismatches.
- Builder writes registry-declared features only (CI-enforced).
- Leakage battery runs as a **pre-training pipeline stage** as well as CI.
- Final artifact refit on all eligible data after CV/backtest estimate.
- Hyperparameters: fixed defaults or tiny grid (N=76 — search overfits
  the protocol). Fixed seeds; seed recorded in registry.

## 9. Serving contract
**gold.prediction_player_valuation** (player × model_version):
predicted_value_eur, value_gap_eur, top-k SHAP payload, feature_version,
scored_at.
**gold.prediction_match_outcome** (match × model_version): p_home/p_draw/
p_away — knockout rows carry p_draw = 0 structurally — cutoff_ts, versions.

API read models: GET /v1/players/{id}/valuation; GET /v1/valuations
?sort=value_gap (scout shortlist = story 1); GET /v1/matches/{id}/prediction.
Rules: every response carries model_version + feature_version + scored_at;
TBD-opponent match → explicit not_predictable state with reason (never null,
never fake probability); unscored ≠ unpredictable, structurally distinct.

## 10. MLOps
- **Registry:** model_registry table + versioned artifact directory.
  Entry: model_id, task, semver, pinned feature_version, training snapshot
  identity (bronze load_ids), git commit, hyperparams, metrics JSON, seed,
  status ∈ {candidate, production, archived}. MLflow = future extension.
- **Promotion:** candidate → production only through evaluation gate;
  status changes recorded → "what served on date X" always answerable.
- **Reproducibility contract (CI-runnable):** same commit + load_ids +
  feature_version + seed ⇒ same metrics within float tolerance.
- **CI:** leakage battery, feature/model registry audits, smoke-train on
  sample per PR (pipeline health without full retrain).
