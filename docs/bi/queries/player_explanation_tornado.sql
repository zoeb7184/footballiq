-- Dashboard 2 drill-through: per-player SHAP explanation (tornado + bridge).
-- {{player_id}} is a Metabase variable (the player's natural id). Rows are the
-- feature contributions; multiplicative_factor (= exp(shap_log)) drives the
-- tornado, shap_log drives the baseline->prediction bridge. Attributional
-- language only: the model associates these features with its valuation.
-- Prediction columns are DOUBLE PRECISION, so cast to numeric before ROUND.
SELECT e.feature_name, e.rank,
       e.feature_value,
       ROUND(e.shap_log::numeric, 4)              AS shap_log,
       ROUND(e.multiplicative_factor::numeric, 3) AS mult_factor,
       ROUND(((e.multiplicative_factor - 1) * 100)::numeric, 1) AS pct_effect,
       pr.baseline_log,
       ROUND((pr.predicted_value_eur / 1e6)::numeric, 1) AS predicted_m_eur,
       ROUND((pr.market_value_eur    / 1e6)::numeric, 1) AS market_m_eur,
       pr.model_version, pr.scored_at
FROM gold.explanation_player_valuation e
JOIN gold.dim_player dp                   ON dp.player_sk = e.player_sk
JOIN gold.prediction_player_valuation pr  ON pr.player_sk = e.player_sk
WHERE dp.player_id_nat = {{player_id}}
ORDER BY e.rank
