"""Model performance endpoint tests — ring 1 (fake read model, no DB)."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from footballiq.api.main import create_app
from footballiq.application.model_performance import ModelPerformanceQueries
from footballiq.application.read_models import (
    FeatureImportanceRow,
    ModelPerformanceReadModel,
    ModelRegistryEntry,
)
from footballiq.infrastructure.config import Settings

_DEV_KEY = "test-key"
_DEV_HASH = hashlib.sha256(_DEV_KEY.encode()).hexdigest()
_AUTH = {"X-API-Key": _DEV_KEY}

_ENTRY = ModelRegistryEntry(
    model_id="m-1",
    task="player_valuation",
    version="1.0.0",
    feature_version="1.0.0",
    git_commit="c62341e",
    params={"n_estimators": 400, "max_depth": 4},
    metrics={
        "xgboost": {"rmsle": 0.9369, "mdape": 0.4983, "within_20pct": 0.2003},
        "baseline_median": {"rmsle": 1.6983, "mdape": 0.875, "within_20pct": 0.0897},
    },
    seed=42,
    status="production",
    created_at="2026-07-06T00:00:00Z",
)

_IMPORTANCE = [
    FeatureImportanceRow("caps", 0.41, 33.2, 1248),
    FeatureImportanceRow("age_years", 0.29, 26.1, 1248),
]


class _FakePerformance(ModelPerformanceReadModel):
    def __init__(self, *, empty: bool = False) -> None:
        self._empty = empty

    def list_registry_entries(self, *, task: str) -> list[ModelRegistryEntry]:
        return [] if self._empty or task != "player_valuation" else [_ENTRY]

    def feature_importance(self) -> list[FeatureImportanceRow]:
        return list(_IMPORTANCE)


def _client(*, empty: bool = False) -> TestClient:
    settings = Settings(
        database_url="sqlite://", data_dir=Path("data/raw"), api_key_hashes=(_DEV_HASH,)
    )
    app = create_app(settings)
    app.state.model_performance_queries = ModelPerformanceQueries(
        _FakePerformance(empty=empty)
    )
    return TestClient(app, raise_server_exceptions=False)


def test_requires_api_key() -> None:
    assert _client().get("/v1/models/performance").status_code == 401


def test_report_carries_lineage_metrics_and_importance() -> None:
    resp = _client().get("/v1/models/performance", headers=_AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["task"] == "player_valuation"
    model = data["models"][0]
    assert model["version"] == "1.0.0"
    assert model["git_commit"] == "c62341e"
    assert "baseline_median" in model["metrics"]  # baselines ship with the report
    names = [f["feature_name"] for f in data["feature_importance"]]
    assert names == ["caps", "age_years"]  # ordered by importance
    assert "accuracy_note" in data


def test_empty_registry_is_404_problem() -> None:
    resp = _client(empty=True).get("/v1/models/performance", headers=_AUTH)
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
