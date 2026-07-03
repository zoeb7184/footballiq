"""Gold adapter for model valuations and their SHAP explanations.

Reads the two scoring tables (XAI design §3): prediction_player_valuation for
headline numbers + denormalized top-k, explanation_player_valuation for the
full long-format breakdown. Both are joined to dim_player for display names.
Prediction-as-data: no model runs here — the API only reads what scoring wrote.
"""

from __future__ import annotations

import json

from sqlalchemy import Engine, text
from sqlalchemy.engine import RowMapping

from footballiq.application.read_models import (
    ExplanationRecord,
    ShapContribution,
    ValuationFilter,
    ValuationReadModel,
    ValuationRecord,
)

# Whitelist: request sort key -> column. Guards the ORDER BY against injection.
_SORT_COLUMNS = {
    "value_gap": "pr.value_gap_eur",
    "predicted_value": "pr.predicted_value_eur",
    "market_value": "pr.market_value_eur",
}

_PREDICTION_SELECT = """
SELECT
    dp.player_id_nat, dp.player_name, dp.position,
    pr.market_value_eur, pr.predicted_value_eur, pr.value_gap_eur,
    pr.baseline_log, pr.top_k_json,
    pr.model_version, pr.feature_version, pr.scored_at
FROM {p}prediction_player_valuation pr
JOIN {p}dim_player dp ON dp.player_sk = pr.player_sk
WHERE dp.player_sk > 0
"""


def _contribution(feature_name: str, feature_value: object, shap_log: object,
                  factor: object, rank: object) -> ShapContribution:
    return ShapContribution(
        feature_name=feature_name,
        feature_value=float(str(feature_value)),
        shap_log=float(str(shap_log)),
        multiplicative_factor=float(str(factor)),
        rank=int(str(rank)),
    )


def _top_k(top_k_json: object) -> list[ShapContribution]:
    payload = json.loads(str(top_k_json))
    return [
        _contribution(
            e["feature"], e["feature_value"], e["shap_log"],
            e["multiplicative_factor"], e["rank"],
        )
        for e in payload
    ]


def _valuation(row: RowMapping) -> ValuationRecord:
    return ValuationRecord(
        player_id=int(str(row["player_id_nat"])),
        name=str(row["player_name"]),
        position=str(row["position"]),
        market_value_eur=round(float(str(row["market_value_eur"]))),
        predicted_value_eur=float(str(row["predicted_value_eur"])),
        value_gap_eur=float(str(row["value_gap_eur"])),
        model_version=str(row["model_version"]),
        feature_version=str(row["feature_version"]),
        scored_at=str(row["scored_at"]),
        top_k=_top_k(row["top_k_json"]),
    )


class GoldValuationReadModel(ValuationReadModel):
    """Reads gold.prediction_/explanation_player_valuation (reserved excluded)."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._p = f"{schema}." if schema else ""

    def list_valuations(
        self, *, limit: int, offset: int, filters: ValuationFilter
    ) -> list[ValuationRecord]:
        column = _SORT_COLUMNS[filters.sort]  # KeyError caught upstream by queries
        direction = "DESC" if filters.descending else "ASC"
        query = text(
            _PREDICTION_SELECT.format(p=self._p)
            + f" ORDER BY {column} {direction}, dp.player_name"
            + " LIMIT :limit OFFSET :offset"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(
                query, {"limit": limit, "offset": offset}
            ).mappings().all()
        return [_valuation(r) for r in rows]

    def count_valuations(self) -> int:
        query = text(
            f"SELECT count(*) FROM {self._p}prediction_player_valuation pr "
            f"JOIN {self._p}dim_player dp ON dp.player_sk = pr.player_sk "
            "WHERE dp.player_sk > 0"
        )
        with self._engine.connect() as conn:
            return int(conn.execute(query).scalar_one())

    def get_valuation(self, player_id: int) -> ValuationRecord | None:
        query = text(
            _PREDICTION_SELECT.format(p=self._p) + " AND dp.player_id_nat = :pid"
        )
        with self._engine.connect() as conn:
            row = conn.execute(query, {"pid": player_id}).mappings().first()
        return None if row is None else _valuation(row)

    def get_explanation(self, player_id: int) -> ExplanationRecord | None:
        head = text(
            _PREDICTION_SELECT.format(p=self._p) + " AND dp.player_id_nat = :pid"
        )
        with self._engine.connect() as conn:
            row = conn.execute(head, {"pid": player_id}).mappings().first()
            if row is None:
                return None
            long_rows = conn.execute(
                text(
                    "SELECT e.feature_name, e.feature_value, e.shap_log, "
                    "e.multiplicative_factor, e.rank "
                    f"FROM {self._p}explanation_player_valuation e "
                    f"JOIN {self._p}dim_player dp ON dp.player_sk = e.player_sk "
                    "WHERE dp.player_id_nat = :pid ORDER BY e.rank"
                ),
                {"pid": player_id},
            ).mappings().all()
        return ExplanationRecord(
            player_id=int(str(row["player_id_nat"])),
            name=str(row["player_name"]),
            position=str(row["position"]),
            market_value_eur=round(float(str(row["market_value_eur"]))),
            predicted_value_eur=float(str(row["predicted_value_eur"])),
            value_gap_eur=float(str(row["value_gap_eur"])),
            baseline_log=float(str(row["baseline_log"])),
            model_version=str(row["model_version"]),
            feature_version=str(row["feature_version"]),
            scored_at=str(row["scored_at"]),
            contributions=[
                _contribution(
                    str(r["feature_name"]), r["feature_value"], r["shap_log"],
                    r["multiplicative_factor"], r["rank"],
                )
                for r in long_rows
            ],
        )
