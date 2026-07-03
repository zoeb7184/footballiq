-- Dashboard 2: aggregate value gap by position — where the model most
-- disagrees with the market. Mean gap near zero = calibrated on average;
-- large magnitude = systematic over/under-pricing for that position.
-- Prediction columns are DOUBLE PRECISION, so cast to numeric before ROUND.
SELECT dp.position,
       COUNT(*)                                        AS players,
       ROUND((AVG(pr.value_gap_eur)      / 1e6)::numeric, 2) AS avg_gap_m,
       ROUND((AVG(pr.predicted_value_eur)/ 1e6)::numeric, 1) AS avg_predicted_m,
       ROUND((AVG(pr.market_value_eur)   / 1e6)::numeric, 1) AS avg_market_m
FROM gold.prediction_player_valuation pr
JOIN gold.dim_player dp ON dp.player_sk = pr.player_sk
WHERE dp.player_sk > 0
GROUP BY dp.position
ORDER BY avg_gap_m DESC
