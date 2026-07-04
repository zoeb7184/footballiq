"""Graph endpoint tests — fake read model + SQLite adapter fixture.

Covers the graph serving contract (graph-design §4): edge list, club supplier
ranking with sort, nation supply-concentration (HHI + shares), and the
unknown-nation 404.
"""

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text

from footballiq.api.main import create_app
from footballiq.application.queries import GraphQueries, UnknownSortError
from footballiq.application.read_models import (
    ClubFilter,
    ClubMetric,
    GraphReadModel,
    NationConcentration,
    SupplierShare,
    TalentFlowEdge,
)
from footballiq.infrastructure.config import Settings
from footballiq.infrastructure.gold.graph import GoldGraphReadModel

_KEY = "test-key"
_AUTH = {"X-API-Key": _KEY}

_EDGES = [TalentFlowEdge("Real Madrid", 101, "Spain", 2, 150.0)]
_CLUBS = [ClubMetric("Real Madrid", 2, 3, 230.0)]
_NATION = NationConcentration(
    nation_id=101, nation_name="Spain", supplier_count=2, players_total=3,
    total_value=180.0, hhi_players=5 / 9,
    top_suppliers=[SupplierShare("Real Madrid", 2, 150.0, 2 / 3)],
)


class _Fake(GraphReadModel):
    def list_edges(self, *, limit: int, offset: int) -> list[TalentFlowEdge]:
        return _EDGES[offset : offset + limit]

    def count_edges(self) -> int:
        return 1

    def list_clubs(
        self, *, limit: int, offset: int, filters: ClubFilter
    ) -> list[ClubMetric]:
        assert filters.sort in {"value_exported", "players_supplied", "nations_supplied"}
        return _CLUBS[offset : offset + limit]

    def count_clubs(self) -> int:
        return 1

    def get_nation_concentration(
        self, nation_id: int, *, top: int
    ) -> NationConcentration | None:
        if nation_id != _NATION.nation_id:
            return None
        return replace(_NATION, top_suppliers=_NATION.top_suppliers[:top])


def _client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        data_dir=Path("data/raw"),
        api_key_hashes=(hashlib.sha256(_KEY.encode()).hexdigest(),),
    )
    app = create_app(settings)
    app.state.graph_queries = GraphQueries(_Fake())
    return TestClient(app, raise_server_exceptions=False)


def test_talent_flow_edges() -> None:
    body = _client().get("/v1/graph/talent-flow", headers=_AUTH).json()
    assert body["total"] == 1
    assert body["items"][0]["nation_name"] == "Spain"
    assert body["items"][0]["player_count"] == 2


def test_clubs_ranking_echoes_sort() -> None:
    body = _client().get(
        "/v1/graph/clubs", params={"sort": "value_exported"}, headers=_AUTH
    ).json()
    assert body["sort"] == "value_exported"
    assert body["items"][0]["value_exported"] == 230.0


def test_clubs_invalid_sort_rejected() -> None:
    resp = _client().get("/v1/graph/clubs", params={"sort": "bogus"}, headers=_AUTH)
    assert resp.status_code == 422


def test_nation_concentration_and_404() -> None:
    body = _client().get(
        "/v1/graph/nations/101/supply-concentration", headers=_AUTH
    ).json()
    assert body["hhi_players"] == pytest.approx(5 / 9)
    assert body["top_suppliers"][0]["share"] == pytest.approx(2 / 3)
    assert _client().get(
        "/v1/graph/nations/999/supply-concentration", headers=_AUTH
    ).status_code == 404


def test_graph_requires_auth() -> None:
    assert _client().get("/v1/graph/talent-flow").status_code == 401


def test_queries_reject_unknown_club_sort() -> None:
    with pytest.raises(UnknownSortError):
        GraphQueries(_Fake()).list_clubs(
            limit=10, offset=0, sort="bogus", descending=True
        )


def _warehouse() -> Engine:
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE dim_team (team_sk int, team_id_nat int, team_name text)"
        ))
        conn.execute(text(
            "CREATE TABLE graph_edge_talent_flow (graph_version text, club text, "
            "team_sk int, player_count int, total_value real, computed_at text)"
        ))
        conn.execute(text(
            "CREATE TABLE graph_metrics_club (graph_version text, club text, "
            "nations_supplied int, players_supplied int, value_exported real, "
            "computed_at text)"
        ))
        conn.execute(text(
            "CREATE TABLE graph_metrics_nation (graph_version text, team_sk int, "
            "supplier_count int, players_total int, total_value real, "
            "hhi_players real, computed_at text)"
        ))
        conn.execute(text(
            "INSERT INTO dim_team VALUES (1,101,'Spain'),(2,102,'France')"
        ))
        conn.execute(text(
            "INSERT INTO graph_edge_talent_flow VALUES "
            "('1.0.0','Real Madrid',1,2,150,'t'),('1.0.0','Barcelona',1,1,30,'t'),"
            "('1.0.0','Real Madrid',2,1,80,'t'),('1.0.0','PSG',2,1,40,'t')"
        ))
        conn.execute(text(
            "INSERT INTO graph_metrics_club VALUES "
            "('1.0.0','Real Madrid',2,3,230,'t'),('1.0.0','Barcelona',1,1,30,'t'),"
            "('1.0.0','PSG',1,1,40,'t')"
        ))
        conn.execute(text(
            "INSERT INTO graph_metrics_nation VALUES "
            "('1.0.0',1,2,3,180,0.5555555555555556,'t'),"
            "('1.0.0',2,2,2,120,0.5,'t')"
        ))
    return engine


def test_adapter_edges_ordered_by_value() -> None:
    rm = GoldGraphReadModel(_warehouse(), schema=None)
    top = rm.list_edges(limit=10, offset=0)[0]
    assert (top.club, top.nation_id, top.player_count) == (
        "Real Madrid", 101, 2)  # heaviest total_value (150) first
    assert rm.count_edges() == 4


def test_adapter_clubs_sorted_and_nation_concentration() -> None:
    rm = GoldGraphReadModel(_warehouse(), schema=None)
    clubs = rm.list_clubs(
        limit=10, offset=0, filters=ClubFilter(sort="value_exported", descending=True)
    )
    assert [c.club for c in clubs] == ["Real Madrid", "PSG", "Barcelona"]
    assert rm.count_clubs() == 3

    conc = rm.get_nation_concentration(101, top=10)
    assert conc is not None
    assert conc.hhi_players == pytest.approx(5 / 9)
    assert conc.top_suppliers[0].club == "Real Madrid"
    assert conc.top_suppliers[0].share == pytest.approx(2 / 3)
    assert rm.get_nation_concentration(999, top=10) is None
