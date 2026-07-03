"""Valuation + explanation endpoints (ML design §9 serving contract).

Read-only over the scoring tables. The shortlist (GET /v1/valuations sorted by
value_gap) is scout story 1; the per-player valuation and explanation power the
Dashboard 2 drill-through (tornado + baseline->prediction bridge).
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from footballiq.api.schemas import (
    ExplanationResponse,
    ValuationListResponse,
    ValuationResponse,
)
from footballiq.application.queries import ValuationQueries

router = APIRouter(prefix="/v1", tags=["valuations"])

_Sort = Literal["value_gap", "predicted_value", "market_value"]
_Order = Literal["desc", "asc"]


def get_valuation_queries(request: Request) -> ValuationQueries:
    queries: ValuationQueries = request.app.state.valuation_queries
    return queries


@router.get("/valuations", response_model=ValuationListResponse)
def list_valuations(
    queries: Annotated[ValuationQueries, Depends(get_valuation_queries)],
    sort: Annotated[_Sort, Query()] = "value_gap",
    order: Annotated[_Order, Query()] = "desc",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ValuationListResponse:
    """Model valuations, sortable — value_gap descending is the scout shortlist."""
    page = queries.list_valuations(
        limit=limit, offset=offset, sort=sort, descending=order == "desc"
    )
    return ValuationListResponse(
        items=[ValuationResponse.from_record(r) for r in page.items],
        total=page.page.total,
        limit=page.page.limit,
        offset=page.page.offset,
        sort=sort,
        order=order,
    )


@router.get("/players/{player_id}/valuation", response_model=ValuationResponse)
def get_valuation(
    player_id: int,
    queries: Annotated[ValuationQueries, Depends(get_valuation_queries)],
) -> ValuationResponse:
    """One player's valuation with headline attribution."""
    record = queries.get_valuation(player_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"no valuation for player {player_id} (unknown or not yet scored)",
        )
    return ValuationResponse.from_record(record)


@router.get(
    "/players/{player_id}/valuation/explanation",
    response_model=ExplanationResponse,
)
def get_explanation(
    player_id: int,
    queries: Annotated[ValuationQueries, Depends(get_valuation_queries)],
) -> ExplanationResponse:
    """One player's full SHAP breakdown (all features + baseline)."""
    record = queries.get_explanation(player_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"no explanation for player {player_id} (unknown or not yet scored)",
        )
    return ExplanationResponse.from_record(record)
