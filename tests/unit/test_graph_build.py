"""Talent-flow graph tests (graph-design §6).

A tiny hand-computed fixture pins the metrics exactly: club weighted degree /
value exported, nation supplier count / HHI. Plus the two structural checks the
design calls for — edge player_count reconciliation and projection symmetry —
and determinism.
"""

import pytest
from sqlalchemy import Engine, create_engine, text

from footballiq.graph import build


def _warehouse() -> Engine:
    """5 real players across 3 clubs and 2 nations; 1 reserved, 1 clubless."""
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE dim_team (team_sk int, team_name text)"))
        conn.execute(text(
            "CREATE TABLE dim_player (player_sk int, club_team text, team_sk int, "
            "market_value_eur real)"
        ))
        conn.execute(text(
            "INSERT INTO dim_team VALUES (1,'Spain'),(2,'France'),(-1,'Unknown')"
        ))
        conn.execute(text(
            "INSERT INTO dim_player VALUES "
            "(1,'Real Madrid',1,100),(2,'Real Madrid',1,50),(3,'Barcelona',1,30),"
            "(4,'Real Madrid',2,80),(5,'PSG',2,40),"
            "(6,NULL,1,10),(-1,'Reserved',-1,0)"  # clubless + reserved: excluded
        ))
    return engine


def _rows(engine: Engine, sql: str) -> list[dict]:
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text(sql)).mappings()]


def test_build_counts_and_reconciliation() -> None:
    result = build.build_talent_flow(_warehouse(), schema=None)
    assert (result.n_edges, result.n_clubs, result.n_nations) == (4, 3, 2)
    assert result.total_players == 5  # every real, clubbed player = one edge unit


def test_edge_player_count_reconciles_to_squad_total() -> None:
    engine = _warehouse()
    build.build_talent_flow(engine, schema=None)
    total = _rows(engine, "SELECT sum(player_count) AS s FROM graph_edge_talent_flow")
    assert total[0]["s"] == 5


def test_club_metrics_exact() -> None:
    engine = _warehouse()
    build.build_talent_flow(engine, schema=None)
    by_club = {r["club"]: r for r in _rows(
        engine, "SELECT * FROM graph_metrics_club")}
    rm = by_club["Real Madrid"]
    assert rm["nations_supplied"] == 2      # supplies Spain and France
    assert rm["players_supplied"] == 3      # 2 to Spain + 1 to France
    assert rm["value_exported"] == 230.0    # 100 + 50 + 80
    assert by_club["Barcelona"]["players_supplied"] == 1
    assert by_club["PSG"]["value_exported"] == 40.0


def test_nation_hhi_and_suppliers_exact() -> None:
    engine = _warehouse()
    build.build_talent_flow(engine, schema=None)
    by_nation = {r["team_sk"]: r for r in _rows(
        engine, "SELECT * FROM graph_metrics_nation")}
    spain = by_nation[1]
    assert spain["supplier_count"] == 2
    assert spain["players_total"] == 3
    assert spain["total_value"] == 180.0            # 150 (RM) + 30 (Barca)
    assert spain["hhi_players"] == pytest.approx(5 / 9)  # (2/3)^2 + (1/3)^2
    assert by_nation[2]["hhi_players"] == pytest.approx(0.5)  # (1/2)^2 * 2


def test_projection_symmetry() -> None:
    rows = [("Real Madrid", 1, 100.0), ("Real Madrid", 2, 80.0),
            ("PSG", 2, 40.0)]
    graph = build.build_graph(rows)
    proj = build.project_nations(graph)
    n1, n2 = ("nation", 1), ("nation", 2)
    assert proj.has_edge(n1, n2)  # both nations share Real Madrid
    assert proj.has_edge(n2, n1)  # undirected -> symmetric


def test_deterministic_rebuild() -> None:
    engine = _warehouse()
    build.build_talent_flow(engine, schema=None)
    first = _rows(engine, "SELECT club, team_sk, player_count, total_value "
                          "FROM graph_edge_talent_flow ORDER BY club, team_sk")
    build.build_talent_flow(engine, schema=None)
    second = _rows(engine, "SELECT club, team_sk, player_count, total_value "
                           "FROM graph_edge_talent_flow ORDER BY club, team_sk")
    assert first == second
