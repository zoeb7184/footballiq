"""Valuation endpoint tests — fake read model + SQLite adapter fixture.

Covers the serving contract (ML design §9): shortlist sort, per-player
valuation with provenance, full explanation with the additivity invariant
surviving the read path, and the unscored -> 404 state.
"""

import hashlib
import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text

from footballiq.api.main import create_app
from footballiq.application.queries import UnknownSortError, ValuationQueries
from footballiq.application.read_models import (
    ExplanationRecord,
    ShapContribution,
    ValuationFilter,
    ValuationReadModel,
    ValuationRecord,
)
from footballiq.infrastructure.config import Settings
from footballiq.infrastructure.gold.valuations import GoldValuationReadModel

_KEY = "test-key"
_AUTH = {"X-API-Key": _KEY}

_TOP = [
    ShapContribution("caps", 60.0, 0.30, math.exp(0.30), 1),
    ShapContribution("age_years", 24.0, -0.20, math.exp(-0.20), 2),
]
_VAL = ValuationRecord(
    player_id=7, name="Test Player", position="FWD", market_value_eur=40_000_000,
    predicted_value_eur=55_000_000.0, value_gap_eur=15_000_000.0,
    model_version="1.0.0", feature_version="1.0.0",
    scored_at="2026-07-04T00:00:00+00:00", top_k=_TOP,
)


class _Fake(ValuationReadModel):
    def list_valuations(
        self, *, limit: int, offset: int, filters: ValuationFilter
    ) -> list[ValuationRecord]:
        assert filters.sort in {"value_gap", "predicted_value", "market_value"}
        return [_VAL][offset : offset + limit]

    def count_valuations(self) -> int:
        return 1

    def get_valuation(self, player_id: int) -> ValuationRecord | None:
        return _VAL if player_id == _VAL.player_id else None

    def get_explanation(self, player_id: int) -> ExplanationRecord | None:
        if player_id != _VAL.player_id:
            return None
        return ExplanationRecord(
            player_id=7, name="Test Player", position="FWD",
            market_value_eur=40_000_000, predicted_value_eur=55_000_000.0,
            value_gap_eur=15_000_000.0, baseline_log=16.0,
            model_version="1.0.0", feature_version="1.0.0",
            scored_at="2026-07-04T00:00:00+00:00", contributions=_TOP,
        )


def _client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        data_dir=Path("data/raw"),
        api_key_hashes=(hashlib.sha256(_KEY.encode()).hexdigest(),),
    )
    app = create_app(settings)
    app.state.valuation_queries = ValuationQueries(_Fake())
    return TestClient(app, raise_server_exceptions=False)


def test_list_valuations_carries_sort_and_provenance() -> None:
    body = _client().get(
        "/v1/valuations", params={"sort": "value_gap", "order": "desc"}, headers=_AUTH
    ).json()
    assert body["total"] == 1
    assert body["sort"] == "value_gap" and body["order"] == "desc"
    item = body["items"][0]
    assert item["value_gap_eur"] == 15_000_000.0
    assert item["model_version"] == "1.0.0" and "scored_at" in item
    assert item["top_k"][0]["feature_name"] == "caps"


def test_invalid_sort_rejected() -> None:
    resp = _client().get("/v1/valuations", params={"sort": "nonsense"}, headers=_AUTH)
    assert resp.status_code == 422


def test_get_valuation_has_accuracy_note_and_topk() -> None:
    body = _client().get("/v1/players/7/valuation", headers=_AUTH).json()
    assert body["predicted_value_eur"] == 55_000_000.0
    assert "20%" in body["accuracy_note"]
    assert [c["rank"] for c in body["top_k"]] == [1, 2]


def test_explanation_additivity_survives_read_path() -> None:
    body = _client().get("/v1/players/7/valuation/explanation", headers=_AUTH).json()
    recon = body["baseline_log"] + sum(c["shap_log"] for c in body["contributions"])
    assert recon == pytest.approx(16.0 + 0.30 - 0.20)  # baseline + sum(shap_log)


def test_unscored_and_auth() -> None:
    assert _client().get("/v1/players/999/valuation", headers=_AUTH).status_code == 404
    assert _client().get(
        "/v1/players/999/valuation/explanation", headers=_AUTH
    ).status_code == 404
    assert _client().get("/v1/valuations").status_code == 401


def test_queries_reject_unknown_sort() -> None:
    queries = ValuationQueries(_Fake())
    with pytest.raises(UnknownSortError):
        queries.list_valuations(limit=10, offset=0, sort="bogus", descending=True)


def _warehouse() -> Engine:
    engine = create_engine("sqlite://")
    predicted = 100.0
    # baseline + sum(shap) must equal log1p(predicted): derive the last term.
    s1, s2 = 0.30, 0.20
    b = 4.0  # baseline_log
    s3 = math.log1p(predicted) - b - s1 - s2
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE dim_player (player_sk int, player_id_nat int, "
            "player_name text, position text)"
        ))
        conn.execute(text(
            "CREATE TABLE prediction_player_valuation (player_sk int, "
            "model_version text, feature_version text, predicted_value_eur real, "
            "market_value_eur real, value_gap_eur real, top_k_json text, "
            "baseline_log real, scored_at text)"
        ))
        conn.execute(text(
            "CREATE TABLE explanation_player_valuation (player_sk int, "
            "model_version text, feature_version text, feature_name text, "
            "feature_value real, shap_log real, multiplicative_factor real, "
            "rank int, baseline_log real, scored_at text)"
        ))
        conn.execute(text(
            "INSERT INTO dim_player VALUES (1,101,'Alpha','FWD'),(2,102,'Beta','MID'),"
            "(-1,NULL,'Unknown',NULL)"
        ))
        # JSON and timestamps carry colons — bind them as params so text() does
        # not misparse ':60' / ':00' as bind parameters.
        insert_pred = text(
            "INSERT INTO prediction_player_valuation VALUES "
            "(:sk, '1.0.0', '1.0.0', :pred, :mkt, :gap, :tk, 4.0, :sa)"
        )
        conn.execute(insert_pred, [
            {"sk": 1, "pred": 100.0, "mkt": 60.0, "gap": 40.0, "sa": "2026-07-04T00:00:00",
             "tk": json.dumps([{"feature": "caps", "feature_value": 60.0,
                                "shap_log": 0.3, "multiplicative_factor": 1.3499,
                                "rank": 1}])},
            {"sk": 2, "pred": 80.0, "mkt": 90.0, "gap": -10.0, "sa": "2026-07-04T00:00:00",
             "tk": json.dumps([{"feature": "age_years", "feature_value": 30.0,
                                "shap_log": -0.1, "multiplicative_factor": 0.9048,
                                "rank": 1}])},
        ])
        insert_expl = text(
            "INSERT INTO explanation_player_valuation VALUES "
            "(1, '1.0.0', '1.0.0', :fn, :fv, :sl, :mf, :rk, :base, 't')"
        )
        conn.execute(insert_expl, [
            {"fn": "caps", "fv": 60.0, "sl": s1, "mf": math.exp(s1), "rk": 1, "base": b},
            {"fn": "age_years", "fv": 24.0, "sl": s2, "mf": math.exp(s2), "rk": 2, "base": b},
            {"fn": "height_cm", "fv": 185.0, "sl": s3, "mf": math.exp(s3), "rk": 3, "base": b},
        ])
    return engine


def test_adapter_sorts_gap_desc_and_excludes_reserved() -> None:
    rm = GoldValuationReadModel(_warehouse(), schema=None)
    items = rm.list_valuations(
        limit=10, offset=0, filters=ValuationFilter(sort="value_gap", descending=True)
    )
    assert [v.player_id for v in items] == [101, 102]  # gap 40 before -10
    assert rm.count_valuations() == 2  # reserved member invisible
    assert items[0].top_k[0].feature_name == "caps"


def test_adapter_get_and_explanation_reconstructs_prediction() -> None:
    rm = GoldValuationReadModel(_warehouse(), schema=None)
    assert rm.get_valuation(999) is None
    val = rm.get_valuation(101)
    assert val is not None and val.predicted_value_eur == 100.0

    expl = rm.get_explanation(101)
    assert expl is not None
    assert [c.rank for c in expl.contributions] == [1, 2, 3]
    recon = expl.baseline_log + sum(c.shap_log for c in expl.contributions)
    assert recon == pytest.approx(math.log1p(expl.predicted_value_eur))  # additive
