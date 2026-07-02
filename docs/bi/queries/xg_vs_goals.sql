-- Expected vs actual (Dashboard 1 P2): per-team xG vs goals, completed only.
WITH sides AS (
    SELECT f.home_team_sk AS team_sk, f.home_score AS goals, f.home_xg AS xg
    FROM gold.fact_match f WHERE f.status = 'Completed'
    UNION ALL
    SELECT f.away_team_sk, f.away_score, f.away_xg
    FROM gold.fact_match f WHERE f.status = 'Completed'
)
SELECT t.team_name, SUM(goals) AS goals, ROUND(SUM(xg), 2) AS total_xg,
       ROUND(SUM(goals) - SUM(xg), 2) AS overperformance
FROM sides JOIN gold.dim_team t ON sides.team_sk = t.team_sk
GROUP BY t.team_name ORDER BY overperformance DESC
