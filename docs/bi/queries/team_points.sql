-- KPI: Points (kpis.md) — group-stage rules only (3W/1D); knockout awards none.
-- Also returns wins and goal difference for rankings.
WITH sides AS (
    SELECT f.home_team_sk AS team_sk, f.home_score AS gf, f.away_score AS ga,
           s.is_knockout
    FROM gold.fact_match f JOIN gold.dim_stage s ON f.stage_sk = s.stage_sk
    WHERE f.status = 'Completed'
    UNION ALL
    SELECT f.away_team_sk, f.away_score, f.home_score, s.is_knockout
    FROM gold.fact_match f JOIN gold.dim_stage s ON f.stage_sk = s.stage_sk
    WHERE f.status = 'Completed'
)
SELECT
    t.team_name,
    SUM(CASE WHEN NOT is_knockout AND gf > ga THEN 3
             WHEN NOT is_knockout AND gf = ga THEN 1 ELSE 0 END) AS group_points,
    COUNT(*) FILTER (WHERE gf > ga)                              AS wins,
    SUM(gf) - SUM(ga)                                            AS goal_diff,
    COUNT(*)                                                     AS played
FROM sides JOIN gold.dim_team t ON sides.team_sk = t.team_sk
GROUP BY t.team_name
ORDER BY group_points DESC, goal_diff DESC
