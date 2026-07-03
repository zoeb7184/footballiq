"""Player valuation training (ML design sections 5-6).

Baselines first, honestly reported. The production model must beat both
baselines on pooled out-of-fold RMSLE or the evaluation gate refuses to
register it. CV is grouped by national team; the shipped artifact is refit
on all data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import Engine, text

from footballiq.ml.metrics import FloatArray, evaluate
from footballiq.ml.model_registry import register_production_model
from footballiq.ml.registry import VALUATION_FEATURE_VERSION

MODEL_VERSION = "1.0.0"
SEED = 42

NUMERIC_FEATURES: tuple[str, ...] = (
    "age_years", "height_cm", "caps", "international_goals",
    "minutes_played", "appearances", "starts",
    "goals_p90", "assists_p90", "cards_p90", "low_minutes_flag",
    "team_elo", "team_fifa_ranking", "club_count",
)
POSITIONS: tuple[str, ...] = ("GK", "DEF", "MID", "FWD")
FEATURE_COLUMNS: tuple[str, ...] = NUMERIC_FEATURES + tuple(
    f"pos_{p}" for p in POSITIONS
)

XGB_PARAMS: dict[str, Any] = {
    "n_estimators": 400,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "reg_lambda": 1.0,
    "objective": "reg:squarederror",
    "random_state": SEED,
    "n_jobs": 4,
}


class EvaluationGateFailed(RuntimeError):
    """Production model failed to beat the baselines — registration refused."""


@dataclass(frozen=True, slots=True)
class Dataset:
    """Feature matrix + label + CV groups."""

    x: FloatArray
    y_eur: FloatArray
    groups: FloatArray
    positions: list[str]
    player_sks: list[int]
    feature_version: str


def load_dataset(engine: Engine, *, schema: str | None = "gold") -> Dataset:
    """Features ⋈ label. The label joins HERE, at training time — never earlier."""
    p = f"{schema}." if schema else ""
    query = text(
        f"SELECT f.*, d.market_value_eur, d.team_sk "
        f"FROM {p}feature_player_valuation f "
        f"JOIN {p}dim_player d ON d.player_sk = f.player_sk "
        "WHERE f.feature_version = :v ORDER BY f.player_sk"
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"v": VALUATION_FEATURE_VERSION}).mappings().all()
    if not rows:
        msg = "no feature rows — run `make features` first"
        raise RuntimeError(msg)
    positions = [str(r["position"]) for r in rows]
    x = np.array(
        [
            [float(str(r[c])) for c in NUMERIC_FEATURES]
            + [1.0 if pos == p_ else 0.0 for p_ in POSITIONS]
            for r, pos in zip(rows, positions, strict=True)
        ],
        dtype=np.float64,
    )
    return Dataset(
        x=x,
        y_eur=np.array([float(str(r["market_value_eur"])) for r in rows]),
        groups=np.array([float(str(r["team_sk"])) for r in rows]),
        positions=positions,
        player_sks=[int(str(r["player_sk"])) for r in rows],
        feature_version=VALUATION_FEATURE_VERSION,
    )


def _median_baseline(
    train_pos: list[str], train_y: FloatArray, test_pos: list[str]
) -> FloatArray:
    """Predict the position median of the training fold."""
    medians = {
        p: float(np.median(train_y[[tp == p for tp in train_pos]]))
        for p in set(train_pos)
    }
    fallback = float(np.median(train_y))
    return np.array([medians.get(p, fallback) for p in test_pos])


def _linear_model() -> Any:
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), Ridge(alpha=1.0, random_state=SEED))


def _xgb_model(params: dict[str, Any]) -> Any:
    from xgboost import XGBRegressor

    return XGBRegressor(**params)


def cross_validate(
    ds: Dataset, *, params: dict[str, Any] | None = None, n_splits: int = 5
) -> dict[str, dict[str, float]]:
    """Pooled out-of-fold metrics for baselines + production, grouped by team."""
    from sklearn.model_selection import GroupKFold

    params = params or XGB_PARAMS
    y_log = np.log1p(ds.y_eur)
    oof: dict[str, FloatArray] = {
        name: np.zeros_like(ds.y_eur) for name in ("baseline_median", "baseline_linear", "xgboost")
    }
    for train_idx, test_idx in GroupKFold(n_splits=n_splits).split(
        ds.x, y_log, groups=ds.groups
    ):
        train_pos = [ds.positions[i] for i in train_idx]
        test_pos = [ds.positions[i] for i in test_idx]
        oof["baseline_median"][test_idx] = _median_baseline(
            train_pos, ds.y_eur[train_idx], test_pos
        )
        linear = _linear_model()
        linear.fit(ds.x[train_idx], y_log[train_idx])
        oof["baseline_linear"][test_idx] = np.expm1(linear.predict(ds.x[test_idx]))
        xgb = _xgb_model(params)
        xgb.fit(ds.x[train_idx], y_log[train_idx])
        oof["xgboost"][test_idx] = np.expm1(xgb.predict(ds.x[test_idx]))
    return {name: evaluate(ds.y_eur, preds) for name, preds in oof.items()}


def gate_passes(metrics: dict[str, dict[str, float]]) -> bool:
    """ML design §8: production must beat BOTH baselines on RMSLE."""
    prod = metrics["xgboost"]["rmsle"]
    return (
        prod < metrics["baseline_median"]["rmsle"]
        and prod < metrics["baseline_linear"]["rmsle"]
    )


def train_production(
    engine: Engine,
    *,
    schema: str | None = "gold",
    out_dir: Path = Path("artifacts"),
    params: dict[str, Any] | None = None,
    n_splits: int = 5,
) -> dict[str, dict[str, float]]:
    """Full training run: CV → gate → refit on all data → artifact → registry."""
    params = params or XGB_PARAMS
    ds = load_dataset(engine, schema=schema)
    metrics = cross_validate(ds, params=params, n_splits=n_splits)
    if not gate_passes(metrics):
        msg = f"evaluation gate FAILED: {json.dumps(metrics, indent=2)}"
        raise EvaluationGateFailed(msg)

    final = _xgb_model(params)
    final.fit(ds.x, np.log1p(ds.y_eur))
    artifact_dir = out_dir / "valuation" / f"v{MODEL_VERSION}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "model.ubj"
    final.save_model(model_path)
    (artifact_dir / "meta.json").write_text(
        json.dumps(
            {
                "task": "player_valuation",
                "model_version": MODEL_VERSION,
                "feature_version": VALUATION_FEATURE_VERSION,
                "feature_columns": list(FEATURE_COLUMNS),
                "seed": SEED,
                "params": params,
                "cv_metrics": metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    register_production_model(
        engine,
        task="player_valuation",
        version=MODEL_VERSION,
        feature_version=VALUATION_FEATURE_VERSION,
        params=params,
        metrics=metrics,
        seed=SEED,
        artifact_path=str(model_path),
        schema=schema,
    )
    return metrics
