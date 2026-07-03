-- Dashboard 2: value-gap shortlist (scout story 1).
-- Positive gap = model rates the player above market (undervalued by market);
-- negative = overvalued. Sort ascending for bargains, descending for the
-- most overvalued. SHAP explains the model, not the market (~20% within +/-20%).
-- Prediction columns are DOUBLE PRECISION, so cast to numeric before ROUND.
SELECT dp.player_name, t.team_name, dp.position,
       ROUND((pr.market_value_eur    / 1e6)::numeric, 1) AS market_m_eur,
       ROUND((pr.predicted_value_eur / 1e6)::numeric, 1) AS predicted_m_eur,
       ROUND((pr.value_gap_eur       / 1e6)::numeric, 1) AS gap_m_eur,
       pr.model_version, pr.scored_at
FROM gold.prediction_player_valuation pr
JOIN gold.dim_player dp ON dp.player_sk = pr.player_sk
JOIN gold.dim_team   t  ON dp.team_sk   = t.team_sk
WHERE dp.player_sk > 0
ORDER BY pr.value_gap_eur DESC
