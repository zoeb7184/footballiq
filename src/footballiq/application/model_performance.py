"""Model performance use case (ADR-0006): governance as data.

Serves what the platform already records — nothing is computed at request
time and nothing is invented:

- registry entries from ``gold.model_registry`` (versions, params, seed,
  git commit, cross-validated metrics — written at training time), and
- global feature importance aggregated from the per-player SHAP rows in
  ``gold.explanation_player_valuation`` (mean |shap_log| per feature).

The metrics block includes the honest baselines (median, linear) next to
the production model, because "better than what?" is the first question a
reviewer should ask of any model claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from footballiq.application.read_models import (
    FeatureImportanceRow,
    ModelPerformanceReadModel,
    ModelRegistryEntry,
)

_VALUATION_TASK = "player_valuation"


class NoRegisteredModelError(LookupError):
    """The registry holds no models for the requested task."""


@dataclass(frozen=True, slots=True)
class ModelPerformanceReport:
    """Registry lineage plus aggregated explainability for one task."""

    task: str
    models: list[ModelRegistryEntry]
    feature_importance: list[FeatureImportanceRow]


class ModelPerformanceQueries:
    """Read-only access to model governance data."""

    def __init__(self, read_model: ModelPerformanceReadModel) -> None:
        self._read_model = read_model

    def get_report(self, *, task: str = _VALUATION_TASK) -> ModelPerformanceReport:
        entries = self._read_model.list_registry_entries(task=task)
        if not entries:
            msg = f"no registered models for task {task!r}"
            raise NoRegisteredModelError(msg)
        return ModelPerformanceReport(
            task=task,
            models=entries,
            feature_importance=self._read_model.feature_importance(),
        )
