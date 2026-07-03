"""Valuation training tests: metrics, gate, registry, synthetic CV smoke."""

import json

import numpy as np
from sqlalchemy import create_engine, text

from footballiq.ml.metrics import evaluate, mdape, rmsle, within_20pct
from footballiq.ml.model_registry import register_production_model
from footballiq.ml.valuation import (
    Dataset,
    cross_validate,
    gate_passes,
)


def test_metrics_exact_values() -> None:
    y = np.array([100.0, 100.0, 100.0, 100.0])
    pred = np.array([110.0, 90.0, 150.0, 100.0])  # +10%, -10%, +50%, exact
    assert within_20pct(y, pred) == 0.75
    assert mdape(y, pred) == 0.10
    assert rmsle(y, y) == 0.0
    block = evaluate(y, pred)
    assert set(block) == {"rmsle", "mdape", "within_20pct"}


def test_gate_requires_beating_both_baselines() -> None:
    def block(v: float) -> dict[str, float]:
        return {"rmsle": v, "mdape": 0.0, "within_20pct": 0.0}

    good = {"baseline_median": block(1.0), "baseline_linear": block(0.8),
            "xgboost": block(0.7)}
    beats_one = {"baseline_median": block(1.0), "baseline_linear": block(0.6),
                 "xgboost": block(0.7)}
    assert gate_passes(good)
    assert not gate_passes(beats_one)


def test_registry_promotes_and_archives() -> None:
    engine = create_engine("sqlite://")
    common: dict[str, object] = {
        "task": "player_valuation", "feature_version": "1.0.0",
        "params": {"d": 4}, "metrics": {"xgboost": {"rmsle": 0.5}},
        "seed": 42, "artifact_path": "artifacts/x", "schema": None,
    }
    register_production_model(engine, version="1.0.0", **common)  # type: ignore[arg-type]
    register_production_model(engine, version="1.1.0", **common)  # type: ignore[arg-type]
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT version, status, params FROM model_registry ORDER BY created_at")
        ).all()
    assert [(r[0], r[1]) for r in rows] == [("1.0.0", "archived"), ("1.1.0", "production")]
    assert json.loads(rows[0][2]) == {"d": 4}  # lineage survives round-trip


def _synthetic(n: int = 240, teams: int = 12) -> Dataset:
    """Learnable synthetic data: value driven by caps, age, and club_count."""
    rng = np.random.default_rng(42)
    caps = rng.integers(0, 120, n).astype(np.float64)
    age = rng.integers(17, 39, n).astype(np.float64)
    club = rng.integers(1, 8, n).astype(np.float64)
    y = 200_000 * (1 + caps) * np.exp(-0.08 * np.abs(age - 25)) * club
    y *= np.exp(rng.normal(0, 0.25, n))
    positions = [("GK", "DEF", "MID", "FWD")[i % 4] for i in range(n)]
    x = np.zeros((n, 18))
    x[:, 0] = age
    x[:, 1] = 180
    x[:, 2] = caps
    x[:, 13] = club
    for i, pos in enumerate(positions):
        x[i, 14 + ("GK", "DEF", "MID", "FWD").index(pos)] = 1.0
    return Dataset(
        x=x, y_eur=y,
        groups=np.repeat(np.arange(teams, dtype=np.float64), n // teams),
        positions=positions, player_sks=list(range(n)),
    )


def test_cv_smoke_learnable_signal_passes_gate() -> None:
    """Full grouped-CV loop on synthetic data: models learn, gate passes."""
    metrics = cross_validate(
        _synthetic(),
        params={"n_estimators": 60, "max_depth": 3, "learning_rate": 0.15,
                "objective": "reg:squarederror", "random_state": 42, "n_jobs": 2},
        n_splits=4,
    )
    assert set(metrics) == {"baseline_median", "baseline_linear", "xgboost"}
    # signal is real: production must beat both baselines here
    assert gate_passes(metrics), metrics
    assert metrics["xgboost"]["within_20pct"] > metrics["baseline_median"]["within_20pct"]
