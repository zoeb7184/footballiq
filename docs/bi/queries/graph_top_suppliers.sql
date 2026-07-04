-- Dashboard 2 (graph section): top talent-supplier clubs by value exported.
-- Enterprise reading: supplier importance / contract volume (graph-design §2).
-- value_exported is DOUBLE PRECISION, so cast to numeric before ROUND.
SELECT club,
       players_supplied,
       nations_supplied,
       ROUND((value_exported / 1e6)::numeric, 1) AS value_exported_m
FROM gold.graph_metrics_club
ORDER BY value_exported DESC
LIMIT 20
