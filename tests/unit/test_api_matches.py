"""Match endpoint tests — the discriminated-union contract, verified."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from footballiq.api.main import create_app
from footballiq.application.queries import MatchQueries
from footballiq.application.read_models import MatchReadModel, MatchRecord, TeamSide
from footballiq.infrastructure.config import Settings

_KEY = "test-key"
_AUTH = {"X-API-Key": _KEY}

_MEXICO = TeamSide(1, "Mexico", "MEX")
_RSA = TeamSide(2, "South Africa", "RSA")

_COMPLETED = MatchRecord(
    match_id=1, match_date="2026-06-11", kickoff_utc="19:00",
    stage_name="Group Stage", is_knockout=False, venue_name="Estadio Azteca",
    home_team=_MEXICO, away_team=_RSA, status="Completed",
    home_score=2, away_score=0, home_xg=1.84, away_xg=0.52,
)
_SCHEDULED_TBD = MatchRecord(
    match_id=89, match_date="2026-07-04", kickoff_utc="21:00",
    stage_name="Round of 16", is_knockout=True, venue_name="MetLife",
    home_team=_MEXICO, away_team=None, status="Scheduled",
    home_score=None, away_score=None, home_xg=None, away_xg=None,
)


class _FakeMatches(MatchReadModel):
    def __init__(self, records: list[MatchRecord]) -> None:
        self._records = records

    def list_matches(
        self, *, limit: int, offset: int, status: str | None
    ) -> list[MatchRecord]:
        rows = [r for r in self._records if status is None or r.status == status]
        return rows[offset : offset + limit]

    def count_matches(self, *, status: str | None) -> int:
        return len([r for r in self._records if status is None or r.status == status])

    def get_match(self, match_id: int) -> MatchRecord | None:
        return next((r for r in self._records if r.match_id == match_id), None)


def _client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        data_dir=Path("data/raw"),
        api_key_hashes=(hashlib.sha256(_KEY.encode()).hexdigest(),),
    )
    app = create_app(settings)
    app.state.match_queries = MatchQueries(_FakeMatches([_COMPLETED, _SCHEDULED_TBD]))
    return TestClient(app, raise_server_exceptions=False)


def test_completed_match_carries_required_score_and_xg() -> None:
    body = _client().get("/v1/matches/1", headers=_AUTH).json()
    assert body["status"] == "Completed"
    assert body["score"] == {"home": 2, "away": 0}
    assert body["xg"]["home"] == 1.84
    assert body["away"]["kind"] == "team"


def test_scheduled_match_is_structurally_scoreless() -> None:
    body = _client().get("/v1/matches/89", headers=_AUTH).json()
    assert body["status"] == "Scheduled"
    assert "score" not in body  # the contract: no field to lie with
    assert "xg" not in body


def test_tbd_opponent_is_an_explicit_state_not_null() -> None:
    body = _client().get("/v1/matches/89", headers=_AUTH).json()
    assert body["away"] == {"kind": "to_be_determined"}


def test_status_filter_and_pagination() -> None:
    body = _client().get(
        "/v1/matches", params={"status": "Completed"}, headers=_AUTH
    ).json()
    assert body["total"] == 1
    assert body["items"][0]["match_id"] == 1

    bad = _client().get("/v1/matches", params={"status": "Weird"}, headers=_AUTH)
    assert bad.status_code == 422  # enum-validated filter


def test_match_404_and_auth_guard() -> None:
    assert _client().get("/v1/matches/999", headers=_AUTH).status_code == 404
    assert _client().get("/v1/matches").status_code == 401


def test_contract_violation_in_gold_surfaces_as_500() -> None:
    broken = MatchRecord(
        match_id=7, match_date="2026-06-12", kickoff_utc="18:00",
        stage_name="Group Stage", is_knockout=False, venue_name="X",
        home_team=_MEXICO, away_team=_RSA, status="Completed",
        home_score=None, away_score=None, home_xg=None, away_xg=None,  # illegal
    )
    client = _client()
    queries = MatchQueries(_FakeMatches([broken]))
    client.app.state.match_queries = queries  # type: ignore[attr-defined]
    resp = client.get("/v1/matches/7", headers=_AUTH)
    assert resp.status_code == 500  # loud, never a silent half-answer
