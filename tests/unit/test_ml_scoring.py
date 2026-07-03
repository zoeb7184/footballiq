"""SHAP batch scoring tests (XAI design §§2-4).

The invariant under test is additivity: base + sum(phi) must reconstruct the model
margin, and the two gold tables must load together or not at all. Correctness of
the decomposition (multiplicative_factor = exp(shap_log)), the value-gap sign
convention, long-table completeness/ranks, and the denormalized top-k payload
are all checked against a real booster over the real feature ordering.
"""

import json

import numpy as np
import pytest
from sqlalchemy import Engine, create_engine, text

from footballiq.ml import scoring
from footballiq.ml.features import build_valuation_features
from footballiq.ml.model_registry import register_production_model
from footballiq.ml.scoring import (
    FeatureVersionMismatch,
    ScoringAdditivityError,
    run_scoring,
    score_and_load,
)
from footballiq.ml.valuation import FEATURE_COLUMNS, load_dataset

N_FEATURES = len(FEATURE_COLUMNS)


def _warehouse() -> Engine:
    """A tiny SQLite gold star with a valuation label, then built features."""
    engine = create_engine("sqlite://")
    stmts = [
        "CREATE TABLE dim_team (team_sk int, elo_rating int, fifa_ranking int)",
        (
            "CREATE TABLE dim_player (player_sk int, player_name text, position text, "
            "club_team text, market_value_eur real, caps int, date_of_birth text, "
            "height_cm int, international_goals int, team_sk int)"
        ),
        "CREATE TABLE fact_player_match (player_sk int, minutes_played int, is_starting_xi int)",
        "CREATE TABLE fact_match_event (player_sk int, event_type text)",
        "INSERT INTO dim_team VALUES (1, 1810, 14), (2, 1600, 40)",
        (
            "INSERT INTO dim_player VALUES "
            "(1,'A','FWD','Club X',80000000,60,'1998-03-01',185,25,1), "
            "(2,'B','MID','Club X',35000000,40,'1996-09-12',178,8,1), "
            "(3,'C','DEF','Club Y',12000000,55,'1994-05-20',190,3,2), "
            "(4,'D','GK','Club Y',6000000,30,'1992-11-02',192,0,2), "
            "(-1,'Unknown',NULL,NULL,NULL,NULL,NULL,NULL,NULL,-1)"
        ),
        (
            "INSERT INTO fact_player_match VALUES "
            "(1,90,1),(1,90,1),(2,90,1),(2,45,0),(3,90,1),(4,90,1)"
        ),
        (
            "INSERT INTO fact_match_event VALUES "
            "(1,'Goal'),(1,'Goal'),(1,'Assist'),(2,'Assist'),(3,'Yellow Card')"
        ),
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
    build_valuation_features(engine, schema=None)
    return engine


def _fit_booster(x: np.ndarray, y_eur: np.ndarray) -> object:
    """A real (tiny) XGBoost booster fit in the trainer's log1p space."""
    from xgboost import XGBRegressor

    model = XGBRegressor(
        n_estimators=40, max_depth=2, learning_rate=0.2,
        objective="reg:squarederror", random_state=42, n_jobs=1,
    )
    model.fit(x, np.log1p(y_eur))
    return model.get_booster()


def _scored(engine: Engine) -> tuple[list[dict], list[dict], object]:
    ds = load_dataset(engine, schema=None)
    booster = _fit_booster(ds.x, ds.y_eur)
    run = score_and_load(
        engine, booster=booster, x=ds.x, market_value_eur=ds.y_eur,
        player_sks=ds.player_sks, model_version="1.0.0",
        feature_version="1.0.0", schema=None,
    )
    with engine.connect() as conn:
        preds = [dict(r) for r in conn.execute(
            text("SELECT * FROM prediction_player_valuation ORDER BY player_sk")
        ).mappings()]
        expl = [dict(r) for r in conn.execute(
            text("SELECT * FROM explanation_player_valuation "
                 "ORDER BY player_sk, rank")
        ).mappings()]
    return preds, expl, run


def test_both_tables_load_with_expected_cardinality() -> None:
    engine = _warehouse()
    preds, expl, run = _scored(engine)
    n_players = len(preds)
    assert n_players == 4  # reserved member excluded upstream
    assert run.n_predictions == n_players
    assert run.n_explanations == n_players * N_FEATURES
    assert len(expl) == n_players * N_FEATURES


def test_multiplicative_factor_is_exp_of_shap_log() -> None:
    _, expl, _ = _scored(_warehouse())
    for row in expl:
        assert row["multiplicative_factor"] == pytest.approx(
            np.exp(row["shap_log"]), rel=1e-9
        )


def test_additivity_reconstructs_prediction() -> None:
    """base + sum(phi) (long table) = log1p(predicted) for every player."""
    preds, expl, _ = _scored(_warehouse())
    by_player: dict[int, list[dict]] = {}
    for r in expl:
        by_player.setdefault(int(r["player_sk"]), []).append(r)
    for p in preds:
        rows = by_player[int(p["player_sk"])]
        base = rows[0]["baseline_log"]
        recon = base + sum(r["shap_log"] for r in rows)
        assert recon == pytest.approx(
            np.log1p(p["predicted_value_eur"]), abs=1e-4
        )


def test_value_gap_is_predicted_minus_market() -> None:
    preds, _, _ = _scored(_warehouse())
    for p in preds:
        assert p["value_gap_eur"] == pytest.approx(
            p["predicted_value_eur"] - p["market_value_eur"], rel=1e-9
        )


def test_rank_orders_features_by_absolute_shap() -> None:
    _, expl, _ = _scored(_warehouse())
    by_player: dict[int, list[dict]] = {}
    for r in expl:
        by_player.setdefault(int(r["player_sk"]), []).append(r)
    for rows in by_player.values():
        ordered = sorted(rows, key=lambda r: r["rank"])
        mags = [abs(r["shap_log"]) for r in ordered]
        assert mags == sorted(mags, reverse=True)
        assert [r["rank"] for r in ordered] == list(range(1, N_FEATURES + 1))


def test_top_k_payload_matches_long_table_head() -> None:
    preds, expl, _ = _scored(_warehouse())
    by_player: dict[int, list[dict]] = {}
    for r in expl:
        by_player.setdefault(int(r["player_sk"]), []).append(r)
    for p in preds:
        payload = json.loads(p["top_k_json"])
        assert len(payload) == scoring.DEFAULT_TOP_K
        long_top = sorted(by_player[int(p["player_sk"])], key=lambda r: r["rank"])
        for entry, long_row in zip(payload, long_top, strict=False):
            assert entry["feature"] == long_row["feature_name"]
            assert entry["shap_log"] == pytest.approx(long_row["shap_log"], rel=1e-9)
            assert entry["rank"] == long_row["rank"]


def test_additivity_failure_refuses_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """A decomposition that doesn't reconstruct the margin blocks BOTH writes."""
    engine = _warehouse()
    ds = load_dataset(engine, schema=None)
    booster = _fit_booster(ds.x, ds.y_eur)

    real = scoring._tree_shap

    def _corrupt(bst: object, x: np.ndarray) -> tuple:
        phi, base, margin = real(bst, x)
        return phi, base, margin + 1.0  # margin no longer equals base + sum(phi)

    monkeypatch.setattr(scoring, "_tree_shap", _corrupt)
    with pytest.raises(ScoringAdditivityError):
        score_and_load(
            engine, booster=booster, x=ds.x, market_value_eur=ds.y_eur,
            player_sks=ds.player_sks, model_version="1.0.0",
            feature_version="1.0.0", schema=None,
        )
    # neither table was created — the guard runs before any write
    with engine.connect() as conn:
        tables = {
            r[0] for r in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
    assert "prediction_player_valuation" not in tables
    assert "explanation_player_valuation" not in tables


def test_run_scoring_rejects_feature_version_mismatch() -> None:
    """A model pinned to a different feature_version fails before scoring."""
    engine = _warehouse()
    register_production_model(
        engine, task="player_valuation", version="1.0.0",
        feature_version="9.9.9", params={"d": 2},
        metrics={"xgboost": {"rmsle": 0.5}}, seed=42,
        artifact_path="artifacts/does-not-matter.ubj", schema=None,
    )
    with pytest.raises(FeatureVersionMismatch, match="feature_version mismatch"):
        run_scoring(engine, schema=None)
