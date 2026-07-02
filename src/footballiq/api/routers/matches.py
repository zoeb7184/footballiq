"""Match ledger endpoints (/v1/matches)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from footballiq.api.schemas import (
    CompletedMatch,
    MatchListResponse,
    MatchOut,
    ScheduledMatch,
    match_out_from_record,
)
from footballiq.application.queries import MatchQueries

router = APIRouter(prefix="/v1/matches", tags=["matches"])

_StatusFilter = Literal["Scheduled", "Completed"]


def get_match_queries(request: Request) -> MatchQueries:
    queries: MatchQueries = request.app.state.match_queries
    return queries


@router.get("", response_model=MatchListResponse)
def list_matches(
    queries: Annotated[MatchQueries, Depends(get_match_queries)],
    status: Annotated[_StatusFilter | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MatchListResponse:
    """The match ledger, filterable by lifecycle status."""
    page = queries.list_matches(limit=limit, offset=offset, status=status)
    return MatchListResponse(
        items=[match_out_from_record(r) for r in page.items],
        total=page.page.total,
        limit=page.page.limit,
        offset=page.page.offset,
    )


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: int,
    queries: Annotated[MatchQueries, Depends(get_match_queries)],
) -> ScheduledMatch | CompletedMatch:
    """One match; scheduled and completed have structurally different shapes."""
    record = queries.get_match(match_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"match {match_id} not found")
    return match_out_from_record(record)
