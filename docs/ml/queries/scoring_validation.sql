-- Scoring sanity check (M5 Slice 3) — run after `make score`.
--   psql "postgresql://fiq:fiq_local_dev@localhost:5432/footballiq" \
--        -f docs/ml/queries/scoring_validation.sql
-- Read-only. Reconstructs the additivity invariant independently in SQL,
-- so it double-checks the Python write-time guard from the warehouse side.

\pset numericlocale on
\pset null '<NULL>'

\echo '================ 1. TOP 10 UNDERVALUED (model > market) ================'
SELECT pr.player_sk,
       dp.player_name,
       dp.position,
       round(pr.market_value_eur::numeric, 0)    AS market_eur,
       round(pr.predicted_value_eur::numeric, 0)  AS predicted_eur,
       round(pr.value_gap_eur::numeric, 0)        AS gap_eur
FROM gold.prediction_player_valuation pr
JOIN gold.dim_player dp ON dp.player_sk = pr.player_sk
ORDER BY pr.value_gap_eur DESC
LIMIT 10;

\echo '================ 2. TOP 10 OVERVALUED (market > model) ================='
SELECT pr.player_sk,
       dp.player_name,
       dp.position,
       round(pr.market_value_eur::numeric, 0)    AS market_eur,
       round(pr.predicted_value_eur::numeric, 0)  AS predicted_eur,
       round(pr.value_gap_eur::numeric, 0)        AS gap_eur
FROM gold.prediction_player_valuation pr
JOIN gold.dim_player dp ON dp.player_sk = pr.player_sk
ORDER BY pr.value_gap_eur ASC
LIMIT 10;

\echo '================ 3. SUMMARY STATS (predicted & gap, EUR) ==============='
SELECT metric,
       round(min(v)::numeric, 0)                                          AS min,
       round(percentile_cont(0.05) WITHIN GROUP (ORDER BY v)::numeric, 0) AS p05,
       round(percentile_cont(0.25) WITHIN GROUP (ORDER BY v)::numeric, 0) AS p25,
       round(percentile_cont(0.50) WITHIN GROUP (ORDER BY v)::numeric, 0) AS median,
       round(avg(v)::numeric, 0)                                          AS mean,
       round(percentile_cont(0.75) WITHIN GROUP (ORDER BY v)::numeric, 0) AS p75,
       round(percentile_cont(0.95) WITHIN GROUP (ORDER BY v)::numeric, 0) AS p95,
       round(max(v)::numeric, 0)                                          AS max
FROM (
    SELECT 'predicted_value_eur' AS metric, predicted_value_eur AS v
    FROM gold.prediction_player_valuation
    UNION ALL
    SELECT 'value_gap_eur', value_gap_eur
    FROM gold.prediction_player_valuation
) s
GROUP BY metric
ORDER BY metric;

\echo '================ 4. INTEGRITY: nulls / dupes / sanity ================='
SELECT
    count(*)                                                       AS n_rows,
    count(DISTINCT player_sk)                                      AS n_distinct_players,
    count(*) FILTER (WHERE predicted_value_eur IS NULL)            AS null_predicted,
    count(*) FILTER (WHERE value_gap_eur IS NULL)                  AS null_gap,
    count(*) FILTER (WHERE market_value_eur IS NULL)               AS null_market,
    count(*) FILTER (WHERE player_sk <= 0)                         AS reserved_leaked,
    count(*) FILTER (WHERE predicted_value_eur <= 0)               AS nonpositive_pred,
    count(*) FILTER (WHERE predicted_value_eur > 500000000)        AS pred_over_500m
FROM gold.prediction_player_valuation;

\echo '-- duplicate player_sk (expect zero rows) --'
SELECT player_sk, count(*) AS n
FROM gold.prediction_player_valuation
GROUP BY player_sk
HAVING count(*) > 1;

\echo '================ 5. EXPLANATION TABLE shape + additivity =============='
SELECT
    (SELECT count(*) FROM gold.explanation_player_valuation)              AS expl_rows,
    (SELECT count(DISTINCT player_sk) FROM gold.explanation_player_valuation) AS expl_players,
    (SELECT count(DISTINCT feature_name) FROM gold.explanation_player_valuation) AS features_per_player,
    (SELECT count(*) FROM gold.explanation_player_valuation
       WHERE shap_log IS NULL OR multiplicative_factor IS NULL)           AS null_shap;

\echo '-- worst additivity residual across all players (expect ~0, < 1e-4) --'
SELECT round(max(abs(recon - ln(1 + predicted)))::numeric, 8) AS worst_residual
FROM (
    SELECT e.player_sk,
           max(e.baseline_log) + sum(e.shap_log) AS recon,     -- baseline is constant per player
           max(pr.predicted_value_eur)           AS predicted
    FROM gold.explanation_player_valuation e
    JOIN gold.prediction_player_valuation pr ON pr.player_sk = e.player_sk
    GROUP BY e.player_sk
) t;

\echo '-- multiplicative_factor = exp(shap_log)? worst deviation (expect ~0) --'
SELECT round(max(abs(multiplicative_factor - exp(shap_log)))::numeric, 12) AS worst_dev
FROM gold.explanation_player_valuation;
