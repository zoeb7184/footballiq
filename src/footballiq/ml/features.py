"""Valuation feature builder — set-based SQL into gold.feature_player_valuation.

Cross-sectional model (ML design §2A): label and features are one snapshot,
so no as-of cutoffs apply here. The SQL below must never reference the
label — enforced by test_ml_leakage.py against FORBIDDEN_LABEL_TOKENS.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Engine, text

from footballiq.ml.registry import VALUATION_FEATURE_VERSION

_TOURNAMENT_START = "2026-06-11"

# Dialect-specific age expression (PG for production, SQLite for tests).
_AGE_EXPR = {
    "postgresql": (
        f"date_part('year', age(DATE '{_TOURNAMENT_START}', p.date_of_birth))"
    ),
    "sqlite": (
        f"CAST((julianday('{_TOURNAMENT_START}') - julianday(p.date_of_birth))"
        " / 365.25 AS INTEGER)"
    ),
}

_DDL = """
CREATE TABLE {p}feature_player_valuation (
    player_sk           INTEGER NOT NULL,
    feature_version     TEXT NOT NULL,
    computed_at         TEXT NOT NULL,
    age_years           INTEGER NOT NULL,
    height_cm           INTEGER NOT NULL,
    caps                INTEGER NOT NULL,
    international_goals INTEGER NOT NULL,
    position            TEXT NOT NULL,
    minutes_played      INTEGER NOT NULL,
    appearances         INTEGER NOT NULL,
    starts              INTEGER NOT NULL,
    goals_p90           DOUBLE PRECISION NOT NULL,
    assists_p90         DOUBLE PRECISION NOT NULL,
    cards_p90           DOUBLE PRECISION NOT NULL,
    low_minutes_flag    INTEGER NOT NULL,
    team_elo            INTEGER NOT NULL,
    team_fifa_ranking   INTEGER NOT NULL,
    club_count          INTEGER NOT NULL,
    PRIMARY KEY (player_sk, feature_version)
)
"""

_INSERT = """
INSERT INTO {p}feature_player_valuation
WITH minutes AS (
    SELECT player_sk,
           SUM(minutes_played)                                AS minutes_played,
           COUNT(*) FILTER (WHERE minutes_played > 0)         AS appearances,
           SUM(CASE WHEN is_starting_xi THEN 1 ELSE 0 END)    AS starts
    FROM {p}fact_player_match
    GROUP BY player_sk
),
events AS (
    SELECT player_sk,
           COUNT(*) FILTER (WHERE event_type = 'Goal')        AS goals,
           COUNT(*) FILTER (WHERE event_type = 'Assist')      AS assists,
           COUNT(*) FILTER (WHERE event_type IN
               ('Yellow Card', 'Red Card'))                   AS cards
    FROM {p}fact_match_event
    GROUP BY player_sk
),
raw AS (
    SELECT
        p.player_sk,
        {age_expr}                                            AS age_years,
        p.height_cm,
        p.caps,
        p.international_goals,
        p.position,
        COALESCE(m.minutes_played, 0)                         AS minutes_played,
        COALESCE(m.appearances, 0)                            AS appearances,
        COALESCE(m.starts, 0)                                 AS starts,
        CASE WHEN COALESCE(m.minutes_played, 0) >= 90
             THEN COALESCE(e.goals, 0) * 90.0 / m.minutes_played END   AS goals_p90_raw,
        CASE WHEN COALESCE(m.minutes_played, 0) >= 90
             THEN COALESCE(e.assists, 0) * 90.0 / m.minutes_played END AS assists_p90_raw,
        CASE WHEN COALESCE(m.minutes_played, 0) >= 90
             THEN COALESCE(e.cards, 0) * 90.0 / m.minutes_played END   AS cards_p90_raw,
        CASE WHEN COALESCE(m.minutes_played, 0) < 90 THEN 1 ELSE 0 END AS low_minutes_flag,
        t.elo_rating                                          AS team_elo,
        t.fifa_ranking                                        AS team_fifa_ranking,
        COUNT(*) OVER (PARTITION BY p.club_team)              AS club_count
    FROM {p}dim_player p
    JOIN {p}dim_team t ON p.team_sk = t.team_sk
    LEFT JOIN minutes m ON m.player_sk = p.player_sk
    LEFT JOIN events e ON e.player_sk = p.player_sk
    WHERE p.player_sk > 0
)
SELECT
    player_sk,
    :fversion                                                 AS feature_version,
    :computed_at                                              AS computed_at,
    age_years, height_cm, caps, international_goals, position,
    minutes_played, appearances, starts,
    -- <90-minute players: shrink per-90 rates to their position mean (flagged)
    COALESCE(goals_p90_raw,
             AVG(goals_p90_raw) OVER (PARTITION BY position), 0)   AS goals_p90,
    COALESCE(assists_p90_raw,
             AVG(assists_p90_raw) OVER (PARTITION BY position), 0) AS assists_p90,
    COALESCE(cards_p90_raw,
             AVG(cards_p90_raw) OVER (PARTITION BY position), 0)   AS cards_p90,
    low_minutes_flag, team_elo, team_fifa_ranking, club_count
FROM raw
"""


def build_valuation_features(engine: Engine, *, schema: str | None = "gold") -> int:
    """(Re)build the valuation feature table. Deterministic; returns row count."""
    p = f"{schema}." if schema else ""
    age_expr = _AGE_EXPR[engine.dialect.name]
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {p}feature_player_valuation"))
        conn.execute(text(_DDL.format(p=p)))
        conn.execute(
            text(_INSERT.format(p=p, age_expr=age_expr)),
            {
                "fversion": VALUATION_FEATURE_VERSION,
                "computed_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        count = conn.execute(
            text(f"SELECT count(*) FROM {p}feature_player_valuation")
        ).scalar_one()
    return int(count)
