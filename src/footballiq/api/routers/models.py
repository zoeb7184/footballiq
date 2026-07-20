"""Model governance endpoint: GET /v1/models/performance (ADR-0006).

Serves training-time evaluation from the model registry plus global
feature importance aggregated from stored SHAP rows. Read-only; nothing
is computed or invented at request time.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from footballiq.api.schemas import ModelPerformanceResponse
from footballiq.application.model_performance import (
    ModelPerformanceQueries,
    NoRegisteredModelError,
)

router = APIRouter(prefix="/v1/models", tags=["models"])


def get_model_performance_queries(request: Request) -> ModelPerformanceQueries:
    queries: ModelPerformanceQueries = request.app.state.model_performance_queries
    return queries


@router.get("/performance", response_model=ModelPerformanceResponse)
def get_performance(
    queries: Annotated[ModelPerformanceQueries, Depends(get_model_performance_queries)],
) -> ModelPerformanceResponse:
    """Registry lineage (versions, params, CV metrics vs baselines) + mean |SHAP|."""
    try:
        report = queries.get_report()
    except NoRegisteredModelError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ModelPerformanceResponse.from_report(report)
