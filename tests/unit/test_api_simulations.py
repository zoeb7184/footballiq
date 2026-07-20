"""Simulation endpoint tests — ring 1 (fake read models, no DB)."""

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from footballiq.api.main import create_app
from footballiq.application.read_models import (
    ScoringRate,
    ScoringRateReadModel,
    TeamReadModel,
    TeamRecord,
)
from footballiq.application.simulation import SimulationService
from footballiq.infrastructure.config import Settings

_DEV_KEY = "test-key"
_DEV_HASH = hashlib.sha256(_DEV_KEY.encode()).hexdigest()
_AUTH = {"X-API-Key": _DEV_KEY}

_TEAMS = [
    TeamRecord(1, "Spain", "ESP", "E", "UEFA", 3, 2048),
    TeamRecord(2, "Panama", "PAN", "F", "CONCACAF", 43, 1648),
    TeamRecord(3, "Mystery FC", "MYS", None, None, None, None),  # no Elo
]


class _FakeTeams(TeamReadModel):
    def list_teams(self, *, limit: int, offset: int) -> list[TeamRecord]:
        return _TEAMS[offset : offset + limit]

    def count_teams(self) -> int:
        return len(_TEAMS)

    def get_team(self, team_id: int) -> TeamRecord | None:
        return next((t for t in _TEAMS if t.team_id == team_id), None)


class _ObservedRates(ScoringRateReadModel):
    def observed_scoring_rate(self) -> ScoringRate | None:
        return ScoringRate(avg_total_goals=2.5, matches_observed=48)


class _NoRates(ScoringRateReadModel):
    def observed_scoring_rate(self) -> ScoringRate | None:
        return None


def _client(rates: ScoringRateReadModel | None = None) -> TestClient:
    settings = Settings(
        database_url="sqlite://", data_dir=Path("data/raw"), api_key_hashes=(_DEV_HASH,)
    )
    app = create_app(settings)
    app.state.simulation_service = SimulationService(
        _FakeTeams(), rates if rates is not None else _ObservedRates()
    )
    return TestClient(app, raise_server_exceptions=False)


def _simulate(client: TestClient, **overrides: int) -> dict:  # type: ignore[type-arg]
    body = {"home_team_id": 1, "away_team_id": 2, "n_runs": 2000, "seed": 7}
    body.update(overrides)
    resp = client.post("/v1/simulations/match", json=body, headers=_AUTH)
    assert resp.status_code == 200, resp.text
    return dict(resp.json())


def test_requires_api_key() -> None:
    resp = _client().post(
        "/v1/simulations/match", json={"home_team_id": 1, "away_team_id": 2}
    )
    assert resp.status_code == 401


def test_probabilities_sum_to_one_and_carry_intervals() -> None:
    data = _simulate(_client())
    total = data["p_home_win"]["value"] + data["p_draw"]["value"] + data["p_away_win"]["value"]
    assert total == pytest.approx(1.0)
    for key in ("p_home_win", "p_draw", "p_away_win"):
        prob = data[key]
        assert prob["ci_low"] <= prob["value"] <= prob["ci_high"]


def test_stronger_team_is_favoured() -> None:
    data = _simulate(_client())  # Spain (2048) vs Panama (1648)
    assert data["p_home_win"]["value"] > data["p_away_win"]["value"]
    assert data["elo_win_expectancy_home"] > 0.5


def test_identical_seed_means_identical_response() -> None:
    client = _client()
    assert _simulate(client) == _simulate(client)


def test_different_seeds_differ() -> None:
    client = _client()
    assert _simulate(client, seed=7) != _simulate(client, seed=8)


def test_score_matrix_is_a_distribution() -> None:
    data = _simulate(_client())
    cells = [cell for row in data["score_matrix"] for cell in row]
    assert sum(cells) == pytest.approx(1.0)
    assert len(data["score_matrix"]) == data["score_cap"] + 1


def test_observed_rate_is_reported() -> None:
    data = _simulate(_client())
    assert data["goal_rate_source"] == "observed"
    assert data["goals_per_match_used"] == pytest.approx(2.5)
    assert data["matches_observed"] == 48


def test_fallback_rate_is_labeled() -> None:
    data = _simulate(_client(_NoRates()))
    assert data["goal_rate_source"] == "wc2022_baseline"
    assert data["goals_per_match_used"] == pytest.approx(172 / 64)
    assert any("2022" in a for a in data["assumptions"])


def test_unknown_team_is_404_problem() -> None:
    resp = _client().post(
        "/v1/simulations/match",
        json={"home_team_id": 99, "away_team_id": 2},
        headers=_AUTH,
    )
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")


def test_team_without_elo_is_409() -> None:
    resp = _client().post(
        "/v1/simulations/match",
        json={"home_team_id": 1, "away_team_id": 3},
        headers=_AUTH,
    )
    assert resp.status_code == 409


def test_same_team_twice_is_422() -> None:
    resp = _client().post(
        "/v1/simulations/match",
        json={"home_team_id": 1, "away_team_id": 1},
        headers=_AUTH,
    )
    assert resp.status_code == 422


def test_n_runs_out_of_bounds_is_422() -> None:
    resp = _client().post(
        "/v1/simulations/match",
        json={"home_team_id": 1, "away_team_id": 2, "n_runs": 10},
        headers=_AUTH,
    )
    assert resp.status_code == 422
