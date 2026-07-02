-- Headline scalar cards (Dashboard 1 P1). One row; make one Metabase
-- question per column, or use as reference values.
SELECT
    (SELECT ROUND(SUM(market_value_eur) / 1e9, 2)
       FROM gold.dim_player WHERE player_sk > 0)          AS total_value_bn_eur,
    (SELECT COUNT(*) FROM gold.fact_match
      WHERE status = 'Completed')                          AS matches_completed,
    (SELECT SUM(home_score + away_score) FROM gold.fact_match
      WHERE status = 'Completed')                          AS total_goals,
    (SELECT ROUND(AVG(home_score + away_score), 2) FROM gold.fact_match
      WHERE status = 'Completed')                          AS goals_per_match
