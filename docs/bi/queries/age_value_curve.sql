-- Dashboard 2: age vs market value (EUR m), colored by position.
SELECT
    date_part('year', age(DATE '2026-06-11', p.date_of_birth)) AS age,
    ROUND(p.market_value_eur / 1e6, 1) AS value_m_eur,
    p.position,
    p.player_name
FROM gold.dim_player p
WHERE p.player_sk > 0
