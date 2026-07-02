-- Dashboard 2: value distribution by position.
SELECT position,
       ROUND(SUM(market_value_eur) / 1e9, 2)  AS total_value_bn,
       ROUND(AVG(market_value_eur) / 1e6, 1)  AS avg_value_m,
       COUNT(*)                               AS players
FROM gold.dim_player WHERE player_sk > 0
GROUP BY position ORDER BY total_value_bn DESC
