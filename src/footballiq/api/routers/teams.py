"""Team catalog endpoints (/v1/teams)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from footballiq.api.schemas import TeamListResponse, TeamResponse
from footballiq.application.queries import TeamQueries

router = APIRouter(prefix="/v1/teams", tags=["teams"])


def get_team_queries(request: Request) -> TeamQueries:
    queries: TeamQueries = request.app.state.team_queries
    return queries


@router.get("", response_model=TeamListResponse)
def list_teams(
    queries: Annotated[TeamQueries, Depends(get_team_queries)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TeamListResponse:
    """The team catalog, paginated (hard max: 100 per page)."""
    page = queries.list_teams(limit=limit, offset=offset)
    return TeamListResponse(
        items=[TeamResponse.from_record(r) for r in page.items],
        total=page.page.total,
        limit=page.page.limit,
        offset=page.page.offset,
    )


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    queries: Annotated[TeamQueries, Depends(get_team_queries)],
) -> TeamResponse:
    """One team by its natural id; unknown ids are a 404 problem."""
    record = queries.get_team(team_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"team {team_id} not found")
    return TeamResponse.from_record(record)
