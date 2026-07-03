"""SHAP batch scoring (XAI design §§2-4) — predictions and their explanations
are computed in one run and loaded in one transaction.

Canonical additive space is log1p(value_eur): the trainer fits on
``np.log1p(y_eur)``, so TreeSHAP is additive there and ``base + sum(phi)`` equals the
raw model margin exactly. (The design writes "log(value)"; log1p is the honest
implementation — expm1 is the inverse used for the EUR-scale prediction.)

Two gold tables ship together, never apart:
- ``prediction_player_valuation`` — one row per player: predicted_value_eur,
  value_gap_eur, and a denormalized top-k SHAP payload for one-call API reads.
- ``explanation_player_valuation`` — long format (player x feature): shap_log is
  canonical, multiplicative_factor = exp(phi) for display, rank by |phi|, baseline
  stored per row. Required long shape for BI tornado/bridge visuals.

Write-time additivity check: an independent margin (booster ``output_margin``)
must equal ``base + sum(phi)`` within tolerance for every player, or the whole load is
refused. The invariant is enforced, not hoped for.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import Engine, text

from footballiq.ml.metrics import FloatArray
from footballiq.ml.model_registry import load_production_model
from footballiq.ml.valuation import FEATURE_COLUMNS, load_dataset

#: Default number of top-|phi| features denormalized into the prediction payload.
DEFAULT_TOP_K = 5

#: Additivity tolerance in log1p space (float TreeSHAP round-off headroom).
ADDITIVITY_TOL = 1e-4

_PREDICTION_DDL = """
CREATE TABLE {p}prediction_player_valuation (
    player_sk           INTEGER NOT NULL,
    model_version       TEXT NOT NULL,
    feature_version     TEXT NOT NULL,
    predicted_value_eur DOUBLE PRECISION NOT NULL,
    market_value_eur    DOUBLE PRECISION NOT NULL,
    value_gap_eur       DOUBLE PRECISION NOT NULL,
    top_k_json          TEXT NOT NULL,
    baseline_log        DOUBLE PRECISION NOT NULL,
    scored_at           TEXT NOT NULL,
    PRIMARY KEY (player_sk, model_version)
)
"""

_EXPLANATION_DDL = """
CREATE TABLE {p}explanation_player_valuation (
    player_sk           INTEGER NOT NULL,
    model_version       TEXT NOT NULL,
    feature_version     TEXT NOT NULL,
    feature_name        TEXT NOT NULL,
    feature_value       DOUBLE PRECISION NOT NULL,
    shap_log            DOUBLE PRECISION NOT NULL,
    multiplicative_factor DOUBLE PRECISION NOT NULL,
    rank                INTEGER NOT NULL,
    baseline_log        DOUBLE PRECISION NOT NULL,
    scored_at           TEXT NOT NULL,
    PRIMARY KEY (player_sk, model_version, feature_name)
)
"""


class ScoringAdditivityError(RuntimeError):
    """base + sum(phi) != model margin for some player — the load is refused."""


class FeatureVersionMismatch(RuntimeError):
    """The feature table was built at a version the model was not trained on."""


@dataclass(frozen=True, slots=True)
class ScoringRun:
    """What a completed, loaded scoring run produced."""

    model_version: str
    feature_version: str
    n_predictions: int
    n_explanations: int


def _load_booster(artifact_path: str) -> Any:
    """Reload the registered XGBoost model as a Booster for TreeSHAP."""
    import xgboost as xgb

    booster = xgb.Booster()
    booster.load_model(artifact_path)
    return booster


def _tree_shap(
    booster: Any, x: FloatArray
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Exact TreeSHAP via the booster's own ``pred_contribs``.

    Returns (phi[n, f], base[n], margin_direct[n]). The last contrib column is
    the bias (expected margin); ``margin_direct`` is computed independently so
    the caller can assert additivity rather than assume it.
    """
    import xgboost as xgb

    # No feature_names on the DMatrix: the trainer fits on a bare numpy array,
    # so the booster carries default names. Column order (FEATURE_COLUMNS) is the
    # contract shared by training and scoring — names would only risk a mismatch.
    dmatrix = xgb.DMatrix(x)
    contribs = np.asarray(booster.predict(dmatrix, pred_contribs=True), dtype=np.float64)
    phi = contribs[:, :-1]
    base = contribs[:, -1]
    margin_direct = np.asarray(
        booster.predict(dmatrix, output_margin=True), dtype=np.float64
    )
    return phi, base, margin_direct


def _assert_additivity(
    base: FloatArray, phi: FloatArray, margin_direct: FloatArray, *, tol: float
) -> None:
    """base + sum(phi) must reconstruct the independent margin for every player."""
    reconstructed = base + phi.sum(axis=1)
    resid = np.abs(reconstructed - margin_direct)
    worst = float(resid.max()) if resid.size else 0.0
    if worst > tol:
        bad = int(np.argmax(resid))
        msg = (
            f"additivity check failed: |base+sum(phi) - margin| = {worst:.3e} > {tol:.0e} "
            f"at row {bad}; explanation decomposition would not reconstruct the "
            "prediction — refusing to load"
        )
        raise ScoringAdditivityError(msg)


def _top_k_payload(
    names: tuple[str, ...], values: FloatArray, phi_row: FloatArray, k: int
) -> list[dict[str, Any]]:
    """Top-k features for one player by |phi|, ready to serialize into the
    prediction row (one-call API reads, XAI design §3)."""
    order = np.argsort(-np.abs(phi_row))[:k]
    return [
        {
            "feature": names[j],
            "feature_value": float(values[j]),
            "shap_log": float(phi_row[j]),
            "multiplicative_factor": float(np.exp(phi_row[j])),
            "rank": rank,
        }
        for rank, j in enumerate(order, start=1)
    ]


def score_and_load(  # noqa: PLR0913 - the full scoring contract is explicit
    engine: Engine,
    *,
    booster: Any,
    x: FloatArray,
    market_value_eur: FloatArray,
    player_sks: list[int],
    model_version: str,
    feature_version: str,
    schema: str | None = "gold",
    top_k: int = DEFAULT_TOP_K,
    tol: float = ADDITIVITY_TOL,
) -> ScoringRun:
    """Score every player, build the two tables, verify additivity, load atomically.

    Predictions and explanations are dropped-and-written in a single
    transaction: an explanation can never exist without its matching
    prediction, and a failed additivity check leaves both tables untouched.
    """
    phi, base, margin_direct = _tree_shap(booster, x)
    _assert_additivity(base, phi, margin_direct, tol=tol)  # invariant gate

    predicted_eur = np.expm1(margin_direct)
    # Sign convention: predicted minus market. Positive => model rates the
    # player above market (scout shortlist = story 1, sort value_gap descending).
    value_gap = predicted_eur - market_value_eur
    scored_at = datetime.now(tz=UTC).isoformat()
    names = FEATURE_COLUMNS

    prediction_rows: list[dict[str, Any]] = []
    explanation_rows: list[dict[str, Any]] = []
    for i, player_sk in enumerate(player_sks):
        phi_row = phi[i]
        order = np.argsort(-np.abs(phi_row))
        rank_of = {int(j): r for r, j in enumerate(order, start=1)}
        for j, name in enumerate(names):
            explanation_rows.append(
                {
                    "player_sk": player_sk,
                    "model_version": model_version,
                    "feature_version": feature_version,
                    "feature_name": name,
                    "feature_value": float(x[i, j]),
                    "shap_log": float(phi_row[j]),
                    "multiplicative_factor": float(np.exp(phi_row[j])),
                    "rank": rank_of[j],
                    "baseline_log": float(base[i]),
                    "scored_at": scored_at,
                }
            )
        prediction_rows.append(
            {
                "player_sk": player_sk,
                "model_version": model_version,
                "feature_version": feature_version,
                "predicted_value_eur": float(predicted_eur[i]),
                "market_value_eur": float(market_value_eur[i]),
                "value_gap_eur": float(value_gap[i]),
                "top_k_json": json.dumps(_top_k_payload(names, x[i], phi_row, top_k)),
                "baseline_log": float(base[i]),
                "scored_at": scored_at,
            }
        )

    p = f"{schema}." if schema else ""
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {p}explanation_player_valuation"))
        conn.execute(text(f"DROP TABLE IF EXISTS {p}prediction_player_valuation"))
        conn.execute(text(_PREDICTION_DDL.format(p=p)))
        conn.execute(text(_EXPLANATION_DDL.format(p=p)))
        conn.execute(
            text(
                f"INSERT INTO {p}prediction_player_valuation VALUES "
                "(:player_sk, :model_version, :feature_version, :predicted_value_eur, "
                ":market_value_eur, :value_gap_eur, :top_k_json, :baseline_log, "
                ":scored_at)"
            ),
            prediction_rows,
        )
        conn.execute(
            text(
                f"INSERT INTO {p}explanation_player_valuation VALUES "
                "(:player_sk, :model_version, :feature_version, :feature_name, "
                ":feature_value, :shap_log, :multiplicative_factor, :rank, "
                ":baseline_log, :scored_at)"
            ),
            explanation_rows,
        )
    return ScoringRun(
        model_version=model_version,
        feature_version=feature_version,
        n_predictions=len(prediction_rows),
        n_explanations=len(explanation_rows),
    )


def run_scoring(
    engine: Engine,
    *,
    schema: str | None = "gold",
    top_k: int = DEFAULT_TOP_K,
    artifact_override: Path | None = None,
) -> ScoringRun:
    """Load the production model, score all feature rows, load the tables.

    The scoring run pins itself to the registered model_version and
    feature_version; a feature table built at a different version is a load
    failure (feature ordering must match what the model was trained on).
    """
    model = load_production_model(engine, task="player_valuation", schema=schema)
    ds = load_dataset(engine, schema=schema)
    if ds.feature_version != model.feature_version:
        msg = (
            f"feature_version mismatch: model pinned {model.feature_version!r}, "
            f"features are {ds.feature_version!r} — rebuild with `make features`"
        )
        raise FeatureVersionMismatch(msg)
    artifact_path = str(artifact_override) if artifact_override else model.artifact_path
    booster = _load_booster(artifact_path)
    return score_and_load(
        engine,
        booster=booster,
        x=ds.x,
        market_value_eur=ds.y_eur,
        player_sks=ds.player_sks,
        model_version=model.version,
        feature_version=model.feature_version,
        schema=schema,
        top_k=top_k,
    )
