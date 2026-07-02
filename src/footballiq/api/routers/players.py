"""Player registry endpoints (/v1/players)."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from footballiq.api.schemas import PlayerListResponse, PlayerResponse
from footballiq.application.queries import PlayerQueries
from footballiq.application.read_models import PlayerFilter

router = APIRouter(prefix="/v1/players", tags=["players"])

_Position = Literal["GK", "DEF", "MID", "FWD"]


def get_player_queries(request: Request) -> PlayerQueries:
    queries: PlayerQueries = request.app.state.player_queries
    return queries


@router.get("", response_model=PlayerListResponse)
def list_players(
    queries: Annotated[PlayerQueries, Depends(get_player_queries)],
    team_id: Annotated[int | None, Query()] = None,
    position: Annotated[_Position | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PlayerListResponse:
    """The player registry, filterable, ordered by market value descending."""
    page = queries.list_players(
        limit=limit,
        offset=offset,
        filters=PlayerFilter(team_id=team_id, position=position),
    )
    return PlayerListResponse(
        items=[PlayerResponse.from_record(r) for r in page.items],
        total=page.page.total,
        limit=page.page.limit,
        offset=page.page.offset,
    )


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: int,
    queries: Annotated[PlayerQueries, Depends(get_player_queries)],
) -> PlayerResponse:
    """One player by natural id."""
    record = queries.get_player(player_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"player {player_id} not found")
    return PlayerResponse.from_record(record)
