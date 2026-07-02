-- Dashboard 2: top 25 by market value.
SELECT p.player_name, t.team_name, p.position, p.club_team,
       ROUND(p.market_value_eur / 1e6, 1) AS value_m_eur, p.caps
FROM gold.dim_player p JOIN gold.dim_team t ON p.team_sk = t.team_sk
WHERE p.player_sk > 0
ORDER BY p.market_value_eur DESC
LIMIT 25
