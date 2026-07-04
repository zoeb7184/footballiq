-- Dashboard 2 (graph section): nation supplier-concentration risk.
-- hhi_players in (0, 1]: higher = squad drawn from fewer clubs = more
-- concentrated sourcing (graph-design §2). Ranked most-concentrated first.
SELECT t.team_name,
       t.fifa_code,
       n.supplier_count,
       n.players_total,
       ROUND(n.hhi_players::numeric, 3)          AS hhi,
       ROUND((n.total_value / 1e6)::numeric, 1)  AS squad_value_m
FROM gold.graph_metrics_nation n
JOIN gold.dim_team t ON t.team_sk = n.team_sk
WHERE n.team_sk > 0
ORDER BY n.hhi_players DESC
