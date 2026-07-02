-- The primary business question as one picture (Dashboard 1, quadrant):
-- squad value (EUR m) vs group points per team.
WITH sides AS (
    SELECT f.home_team_sk AS team_sk, f.home_score AS gf, f.away_score AS ga,
           s.is_knockout
    FROM gold.fact_match f JOIN gold.dim_stage s ON f.stage_sk = s.stage_sk
    WHERE f.status = 'Completed'
    UNION ALL
    SELECT f.away_team_sk, f.away_score, f.home_score, s.is_knockout
    FROM gold.fact_match f JOIN gold.dim_stage s ON f.stage_sk = s.stage_sk
    WHERE f.status = 'Completed'
),
points AS (
    SELECT team_sk,
           SUM(CASE WHEN NOT is_knockout AND gf > ga THEN 3
                    WHEN NOT is_knockout AND gf = ga THEN 1 ELSE 0 END) AS group_points
    FROM sides GROUP BY team_sk
),
squad AS (
    SELECT team_sk, ROUND(SUM(market_value_eur) / 1e6) AS squad_value_m
    FROM gold.dim_player WHERE player_sk > 0 GROUP BY team_sk
)
SELECT t.team_name, sq.squad_value_m, COALESCE(p.group_points, 0) AS group_points
FROM gold.dim_team t
JOIN squad sq ON sq.team_sk = t.team_sk
LEFT JOIN points p ON p.team_sk = t.team_sk
WHERE t.team_sk > 0
