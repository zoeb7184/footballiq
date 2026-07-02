"""Player endpoint tests — fake read model + SQLite adapter fixture."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from footballiq.api.main import create_app
from footballiq.application.queries import PlayerQueries
from footballiq.application.read_models import (
    PlayerFilter,
    PlayerReadModel,
    PlayerRecord,
    TeamSide,
)
from footballiq.infrastructure.config import Settings
from footballiq.infrastructure.gold.players import GoldPlayerReadModel

_KEY = "test-key"
_AUTH = {"X-API-Key": _KEY}
_MEXICO = TeamSide(1, "Mexico", "MEX")

_PLAYERS = [
    PlayerRecord(16, "Julián Quinones", "FWD", "Club América", 12_000_000,
                 20, 6, "1997-03-24", 178, _MEXICO),
    PlayerRecord(1, "José Raúl Rangel", "GK", "CD Guadalajara", 6_500_000,
                 15, 0, "2000-02-25", 190, _MEXICO),
]


class _Fake(PlayerReadModel):
    def list_players(
        self, *, limit: int, offset: int, filters: PlayerFilter
    ) -> list[PlayerRecord]:
        rows = [
            p for p in _PLAYERS
            if (filters.team_id is None or p.team.team_id == filters.team_id)
            and (filters.position is None or p.position == filters.position)
        ]
        return rows[offset : offset + limit]

    def count_players(self, *, filters: PlayerFilter) -> int:
        return len(self.list_players(limit=10_000, offset=0, filters=filters))

    def get_player(self, player_id: int) -> PlayerRecord | None:
        return next((p for p in _PLAYERS if p.player_id == player_id), None)


def _client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        data_dir=Path("data/raw"),
        api_key_hashes=(hashlib.sha256(_KEY.encode()).hexdigest(),),
    )
    app = create_app(settings)
    app.state.player_queries = PlayerQueries(_Fake())
    return TestClient(app, raise_server_exceptions=False)


def test_list_players_with_position_filter() -> None:
    body = _client().get("/v1/players", params={"position": "GK"}, headers=_AUTH).json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "José Raúl Rangel"
    assert body["items"][0]["team"]["fifa_code"] == "MEX"


def test_invalid_position_rejected() -> None:
    resp = _client().get("/v1/players", params={"position": "STRIKER"}, headers=_AUTH)
    assert resp.status_code == 422


def test_get_player_404_and_auth() -> None:
    assert _client().get("/v1/players/999", headers=_AUTH).status_code == 404
    assert _client().get("/v1/players").status_code == 401


def test_adapter_orders_by_value_and_filters() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE dim_team (team_sk int, team_id_nat int, "
            "team_name text, fifa_code text)"
        ))
        conn.execute(text(
            "CREATE TABLE dim_player (player_sk int, player_id_nat int, "
            "player_name text, position text, club_team text, market_value_eur int, "
            "caps int, international_goals int, date_of_birth text, height_cm int, "
            "team_sk int)"
        ))
        conn.execute(text(
            "INSERT INTO dim_team VALUES (1,1,'Mexico','MEX'), (-1,NULL,'Unknown','UNK')"
        ))
        conn.execute(text(
            "INSERT INTO dim_player VALUES "
            "(1,1,'Rangel','GK','Chivas',6500000,15,0,'2000-02-25',190,1), "
            "(16,16,'Quinones','FWD','América',12000000,20,6,'1997-03-24',178,1), "
            "(-1,NULL,'Unknown',NULL,NULL,NULL,NULL,NULL,NULL,NULL,-1)"
        ))
    rm = GoldPlayerReadModel(engine, schema=None)

    names = [p.name for p in rm.list_players(limit=10, offset=0, filters=PlayerFilter())]
    assert names == ["Quinones", "Rangel"]  # value desc; reserved member invisible
    assert rm.count_players(filters=PlayerFilter(position="GK")) == 1
    found = rm.get_player(16)
    assert found is not None and found.market_value_eur == 12_000_000
    assert rm.get_player(404) is None
