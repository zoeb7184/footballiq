"""Talent-flow graph builder (graph-design §§1-3).

Bipartite club <-> nation graph: an edge means a club supplies player(s) to a
national team; weight = player count, value-weighted variant = sum of market
value. NetworkX computes the metrics in batch; three gold tables are written in
one transaction. Deterministic — no seeds, no sampling.

Cross-confederation edges (graph-design §2) are deferred: clubs are a bare
string with no club->confederation mapping in the warehouse, so that metric is
data-infeasible in MVP (documented in the module report).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import networkx as nx
from sqlalchemy import Engine, text

GRAPH_VERSION = "1.0.0"

# Node keys are typed tuples so club "Ajax" and nation 7 can never collide.
_CLUB = "club"
_NATION = "nation"
# Bipartite side markers (NetworkX convention: two disjoint node sets).
_CLUB_SIDE = 0
_NATION_SIDE = 1

_EDGE_DDL = """
CREATE TABLE {p}graph_edge_talent_flow (
    graph_version  TEXT NOT NULL,
    club           TEXT NOT NULL,
    team_sk        INTEGER NOT NULL,
    player_count   INTEGER NOT NULL,
    total_value    DOUBLE PRECISION NOT NULL,
    computed_at    TEXT NOT NULL,
    PRIMARY KEY (graph_version, club, team_sk)
)
"""

_CLUB_DDL = """
CREATE TABLE {p}graph_metrics_club (
    graph_version    TEXT NOT NULL,
    club             TEXT NOT NULL,
    nations_supplied INTEGER NOT NULL,
    players_supplied INTEGER NOT NULL,
    value_exported   DOUBLE PRECISION NOT NULL,
    computed_at      TEXT NOT NULL,
    PRIMARY KEY (graph_version, club)
)
"""

_NATION_DDL = """
CREATE TABLE {p}graph_metrics_nation (
    graph_version  TEXT NOT NULL,
    team_sk        INTEGER NOT NULL,
    supplier_count INTEGER NOT NULL,
    players_total  INTEGER NOT NULL,
    total_value    DOUBLE PRECISION NOT NULL,
    hhi_players    DOUBLE PRECISION NOT NULL,
    computed_at    TEXT NOT NULL,
    PRIMARY KEY (graph_version, team_sk)
)
"""


@dataclass(frozen=True, slots=True)
class TalentFlowResult:
    """What a completed graph build produced."""

    graph_version: str
    n_edges: int
    n_clubs: int
    n_nations: int
    total_players: int


def _load_rows(engine: Engine, schema: str | None) -> list[tuple[str, int, float]]:
    """(club, team_sk, market_value) for every real player with a club."""
    p = f"{schema}." if schema else ""
    query = text(
        f"SELECT p.club_team, p.team_sk, COALESCE(p.market_value_eur, 0) AS mv "
        f"FROM {p}dim_player p "
        f"JOIN {p}dim_team t ON t.team_sk = p.team_sk "
        "WHERE p.player_sk > 0 AND p.team_sk > 0 AND p.club_team IS NOT NULL "
        "ORDER BY p.club_team, p.team_sk"
    )
    with engine.connect() as conn:
        rows = conn.execute(query).all()
    return [(str(r[0]), int(r[1]), float(r[2])) for r in rows]


def build_graph(rows: list[tuple[str, int, float]]) -> Any:
    """Bipartite club<->nation graph; edge weight = player count, value = sum EUR."""
    graph: Any = nx.Graph()
    for club, team_sk, value in rows:
        c = (_CLUB, club)
        n = (_NATION, team_sk)
        graph.add_node(c, bipartite=_CLUB_SIDE)
        graph.add_node(n, bipartite=_NATION_SIDE)
        if graph.has_edge(c, n):
            graph[c][n]["weight"] += 1
            graph[c][n]["value"] += value
        else:
            graph.add_edge(c, n, weight=1, value=value)
    return graph


def project_nations(graph: Any) -> Any:
    """One-mode nation<->nation projection (shared-club adjacency). Undirected,
    hence structurally symmetric — asserted in tests (graph-design §6)."""
    nations = [x for x, d in graph.nodes(data=True) if d.get("bipartite") == _NATION_SIDE]
    return nx.bipartite.weighted_projected_graph(graph, nations)


def _club_metric_rows(graph: Any, version: str, ts: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node, data in graph.nodes(data=True):
        if data.get("bipartite") != _CLUB_SIDE:
            continue
        out.append({
            "graph_version": version,
            "club": node[1],
            "nations_supplied": graph.degree(node),
            "players_supplied": int(graph.degree(node, weight="weight")),
            "value_exported": float(graph.degree(node, weight="value")),
            "computed_at": ts,
        })
    return out


def _nation_metric_rows(graph: Any, version: str, ts: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node, data in graph.nodes(data=True):
        if data.get("bipartite") != _NATION_SIDE:
            continue
        counts = [int(w) for _, _, w in graph.edges(node, data="weight")]
        total = sum(counts)
        hhi = sum((c / total) ** 2 for c in counts) if total else 0.0
        out.append({
            "graph_version": version,
            "team_sk": node[1],
            "supplier_count": len(counts),
            "players_total": total,
            "total_value": float(graph.degree(node, weight="value")),
            "hhi_players": hhi,
            "computed_at": ts,
        })
    return out


def _edge_rows(graph: Any, version: str, ts: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for u, v, data in graph.edges(data=True):
        club = u[1] if u[0] == _CLUB else v[1]
        team_sk = v[1] if v[0] == _NATION else u[1]
        out.append({
            "graph_version": version,
            "club": club,
            "team_sk": team_sk,
            "player_count": int(data["weight"]),
            "total_value": float(data["value"]),
            "computed_at": ts,
        })
    return out


def build_talent_flow(
    engine: Engine, *, schema: str | None = "gold", version: str = GRAPH_VERSION
) -> TalentFlowResult:
    """Build the graph and load all three gold tables in one transaction."""
    rows = _load_rows(engine, schema)
    if not rows:
        msg = "no player rows — run `make pipeline` first"
        raise RuntimeError(msg)
    graph = build_graph(rows)
    ts = datetime.now(tz=UTC).isoformat()
    edge_rows = _edge_rows(graph, version, ts)
    club_rows = _club_metric_rows(graph, version, ts)
    nation_rows = _nation_metric_rows(graph, version, ts)

    p = f"{schema}." if schema else ""
    with engine.begin() as conn:
        for name, ddl in (
            ("graph_edge_talent_flow", _EDGE_DDL),
            ("graph_metrics_club", _CLUB_DDL),
            ("graph_metrics_nation", _NATION_DDL),
        ):
            conn.execute(text(f"DROP TABLE IF EXISTS {p}{name}"))
            conn.execute(text(ddl.format(p=p)))
        conn.execute(
            text(
                f"INSERT INTO {p}graph_edge_talent_flow VALUES "
                "(:graph_version, :club, :team_sk, :player_count, :total_value, "
                ":computed_at)"
            ),
            edge_rows,
        )
        conn.execute(
            text(
                f"INSERT INTO {p}graph_metrics_club VALUES "
                "(:graph_version, :club, :nations_supplied, :players_supplied, "
                ":value_exported, :computed_at)"
            ),
            club_rows,
        )
        conn.execute(
            text(
                f"INSERT INTO {p}graph_metrics_nation VALUES "
                "(:graph_version, :team_sk, :supplier_count, :players_total, "
                ":total_value, :hhi_players, :computed_at)"
            ),
            nation_rows,
        )
    return TalentFlowResult(
        graph_version=version,
        n_edges=len(edge_rows),
        n_clubs=len(club_rows),
        n_nations=len(nation_rows),
        total_players=sum(r["player_count"] for r in edge_rows),
    )
