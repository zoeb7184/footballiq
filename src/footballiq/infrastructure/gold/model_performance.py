"""Gold adapter for model governance reads (ADR-0006).

Registry rows were written at training time by ``ml.model_registry``;
params/metrics are stored as JSON text and parsed here so the application
layer sees typed records only.
"""

from __future__ import annotations

import json

from sqlalchemy import Engine, text
from sqlalchemy.engine import RowMapping

from footballiq.application.read_models import (
    FeatureImportanceRow,
    ModelPerformanceReadModel,
    ModelRegistryEntry,
)


def _entry(row: RowMapping) -> ModelRegistryEntry:
    return ModelRegistryEntry(
        model_id=str(row["model_id"]),
        task=str(row["task"]),
        version=str(row["version"]),
        feature_version=str(row["feature_version"]),
        git_commit=str(row["git_commit"]),
        params=json.loads(str(row["params"])),
        metrics=json.loads(str(row["metrics"])),
        seed=int(str(row["seed"])),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
    )


class GoldModelPerformanceReadModel(ModelPerformanceReadModel):
    """Reads gold.model_registry + aggregates gold.explanation_player_valuation."""

    def __init__(self, engine: Engine, *, schema: str | None = "gold") -> None:
        self._engine = engine
        self._p = f"{schema}." if schema else ""

    def list_registry_entries(self, *, task: str) -> list[ModelRegistryEntry]:
        query = text(
            "SELECT model_id, task, version, feature_version, git_commit, "
            "params, metrics, seed, status, created_at "
            f"FROM {self._p}model_registry WHERE task = :task "
            "ORDER BY created_at DESC"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(query, {"task": task}).mappings().all()
        return [_entry(r) for r in rows]

    def feature_importance(self) -> list[FeatureImportanceRow]:
        query = text(
            "SELECT feature_name, "
            "avg(abs(shap_log)) AS mean_abs_shap_log, "
            "avg(feature_value) AS mean_feature_value, "
            "count(DISTINCT player_sk) AS players "
            f"FROM {self._p}explanation_player_valuation "
            "GROUP BY feature_name ORDER BY mean_abs_shap_log DESC"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(query).mappings().all()
        return [
            FeatureImportanceRow(
                feature_name=str(r["feature_name"]),
                mean_abs_shap_log=float(str(r["mean_abs_shap_log"])),
                mean_feature_value=float(str(r["mean_feature_value"])),
                players=int(str(r["players"])),
            )
            for r in rows
        ]
