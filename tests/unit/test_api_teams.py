"""Teams endpoint + auth tests — ring 1 (fake read model, no DB)."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from footballiq.api.main import create_app
from footballiq.application.queries import TeamQueries
from footballiq.application.read_models import TeamReadModel, TeamRecord
from footballiq.infrastructure.config import Settings

_DEV_KEY = "test-key"
_DEV_HASH = hashlib.sha256(_DEV_KEY.encode()).hexdigest()
_AUTH = {"X-API-Key": _DEV_KEY}

_TEAMS = [
    TeamRecord(1, "Mexico", "MEX", "A", "CONCACAF", 14, 1810),
    TeamRecord(2, "South Africa", "RSA", "A", "CAF", 60, 1520),
]


class _FakeTeams(TeamReadModel):
    def list_teams(self, *, limit: int, offset: int) -> list[TeamRecord]:
        return _TEAMS[offset : offset + limit]

    def count_teams(self) -> int:
        return len(_TEAMS)

    def get_team(self, team_id: int) -> TeamRecord | None:
        return next((t for t in _TEAMS if t.team_id == team_id), None)


def _client(*, key_hashes: tuple[str, ...] = (_DEV_HASH,)) -> TestClient:
    settings = Settings(
        database_url="sqlite://", data_dir=Path("data/raw"), api_key_hashes=key_hashes
    )
    app = create_app(settings)
    app.state.team_queries = TeamQueries(_FakeTeams())
    return TestClient(app, raise_server_exceptions=False)


def test_missing_key_is_401_problem() -> None:
    resp = _client().get("/v1/teams")
    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/problem+json")


def test_wrong_key_is_401() -> None:
    resp = _client().get("/v1/teams", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_no_configured_keys_means_default_deny() -> None:
    resp = _client(key_hashes=()).get("/v1/teams", headers=_AUTH)
    assert resp.status_code == 401  # never defaults open


def test_list_teams_paginated() -> None:
    resp = _client().get("/v1/teams", params={"limit": 1, "offset": 1}, headers=_AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert [t["name"] for t in body["items"]] == ["South Africa"]


def test_pagination_hard_max_enforced() -> None:
    resp = _client().get("/v1/teams", params={"limit": 500}, headers=_AUTH)
    assert resp.status_code == 422  # backend design §6: hard max


def test_get_team_and_404() -> None:
    ok = _client().get("/v1/teams/1", headers=_AUTH)
    assert ok.status_code == 200
    assert ok.json()["fifa_code"] == "MEX"

    missing = _client().get("/v1/teams/999", headers=_AUTH)
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith("application/problem+json")


def test_system_endpoints_stay_unauthenticated() -> None:
    assert _client().get("/health").status_code == 200
