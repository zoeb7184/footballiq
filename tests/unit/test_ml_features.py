"""Feature layer tests — the leakage battery's first residents.

1. Label-lineage ban: the feature SQL never references the label.
2. Registry completeness: every produced column is declared.
3. Builder semantics on a SQLite star: per-90 math, shrinkage, flags,
   frequency encoding, determinism.
"""

import re

from sqlalchemy import Engine, create_engine, text

from footballiq.ml import features
from footballiq.ml.registry import (
    FORBIDDEN_LABEL_TOKENS,
    VALUATION_FEATURES,
)


def test_label_lineage_ban() -> None:
    """ML design §2A rule 1: no feature may touch market_value."""
    sql_surface = features._DDL + features._INSERT
    names = " ".join(f.name for f in VALUATION_FEATURES)
    for token in FORBIDDEN_LABEL_TOKENS:
        assert token not in sql_surface.lower()
        assert token not in names.lower()


def test_registry_declares_every_produced_column() -> None:
    """Feature registry audit: table columns == declared features (+ keys)."""
    ddl_columns = set(re.findall(r"^\s{4}(\w+)", features._DDL, re.M))
    keys = {"player_sk", "feature_version", "computed_at", "PRIMARY"}
    produced = ddl_columns - keys
    declared = {f.name for f in VALUATION_FEATURES}
    assert produced == declared


def _star() -> Engine:
    engine = create_engine("sqlite://")
    stmts = [
        "CREATE TABLE dim_team (team_sk int, elo_rating int, fifa_ranking int)",
        (
            "CREATE TABLE dim_player (player_sk int, player_name text, position text, "
            "club_team text, caps int, date_of_birth text, height_cm int, "
            "international_goals int, team_sk int)"
        ),
        "CREATE TABLE fact_player_match (player_sk int, minutes_played int, is_starting_xi int)",
        "CREATE TABLE fact_match_event (player_sk int, event_type text)",
        "INSERT INTO dim_team VALUES (1, 1810, 14)",
        # p1: 180 min, 2 goals -> goals_p90 = 1.0; p2: 45 min -> shrunk + flagged
        # p1 & p2 share a club (club_count 2); p3 alone (club_count 1)
        (
            "INSERT INTO dim_player VALUES "
            "(1,'A','FWD','Club X',10,'2000-06-11',180,3,1), "
            "(2,'B','FWD','Club X',5,'1996-01-01',175,1,1), "
            "(3,'C','GK','Club Y',20,'1990-12-31',190,0,1), "
            "(-1,'Unknown',NULL,NULL,NULL,NULL,NULL,NULL,-1)"
        ),
        "INSERT INTO fact_player_match VALUES (1,90,1),(1,90,1),(2,45,0),(3,90,1)",
        "INSERT INTO fact_match_event VALUES (1,'Goal'),(1,'Goal'),(1,'Assist'),(2,'Goal')",
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
    return engine


def _rows(engine: Engine) -> dict[int, dict[str, object]]:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM feature_player_valuation")
        ).mappings().all()
    return {int(str(r["player_sk"])): dict(r) for r in result}


def test_builder_semantics_on_sqlite_star() -> None:
    engine = _star()
    count = features.build_valuation_features(engine, schema=None)
    assert count == 3  # reserved member excluded

    rows = _rows(engine)
    p1, p2, p3 = rows[1], rows[2], rows[3]

    # per-90 math: 2 goals in 180 min -> 1.0 per 90
    assert p1["goals_p90"] == 1.0
    assert p1["low_minutes_flag"] == 0
    assert p1["age_years"] == 26  # born 2000-06-11, reference 2026-06-11

    # shrinkage: p2 (<90 min) inherits FWD position mean (only p1 qualifies)
    assert p2["low_minutes_flag"] == 1
    assert p2["goals_p90"] == p1["goals_p90"]

    # GK with no goals and no >=90 FWD peers in position: falls back to 0? No —
    # p3 has 90 min, so raw applies: 0 goals -> 0.0
    assert p3["goals_p90"] == 0.0

    # frequency encoding
    assert p1["club_count"] == 2 and p2["club_count"] == 2 and p3["club_count"] == 1
    # context join
    assert p1["team_elo"] == 1810 and p1["team_fifa_ranking"] == 14


def test_builder_is_deterministic_and_idempotent() -> None:
    engine = _star()
    features.build_valuation_features(engine, schema=None)
    first = {k: {c: v for c, v in r.items() if c != "computed_at"}
             for k, r in _rows(engine).items()}
    features.build_valuation_features(engine, schema=None)  # rebuild
    second = {k: {c: v for c, v in r.items() if c != "computed_at"}
              for k, r in _rows(engine).items()}
    assert first == second
