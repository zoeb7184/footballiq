"""Talent-flow graph endpoints (graph-design §4).

Read-only over the batch-built graph tables. The edge list doubles as
network-viz data (consumed by the Streamlit portal in M8); the club ranking and
nation supply-concentration back the BI supplier bars and concentration view.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from footballiq.api.schemas import (
    ClubListResponse,
    ClubMetricOut,
    NationConcentrationResponse,
    TalentFlowEdgeOut,
    TalentFlowResponse,
)
from footballiq.application.queries import GraphQueries

router = APIRouter(prefix="/v1/graph", tags=["graph"])

_ClubSort = Literal["value_exported", "players_supplied", "nations_supplied"]
_Order = Literal["desc", "asc"]


def get_graph_queries(request: Request) -> GraphQueries:
    queries: GraphQueries = request.app.state.graph_queries
    return queries


@router.get("/talent-flow", response_model=TalentFlowResponse)
def list_talent_flow(
    queries: Annotated[GraphQueries, Depends(get_graph_queries)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TalentFlowResponse:
    """Club -> nation supply edges, heaviest by exported value first."""
    page = queries.list_edges(limit=limit, offset=offset)
    return TalentFlowResponse(
        items=[TalentFlowEdgeOut.from_record(e) for e in page.items],
        total=page.page.total,
        limit=page.page.limit,
        offset=page.page.offset,
    )


@router.get("/clubs", response_model=ClubListResponse)
def list_clubs(
    queries: Annotated[GraphQueries, Depends(get_graph_queries)],
    sort: Annotated[_ClubSort, Query()] = "value_exported",
    order: Annotated[_Order, Query()] = "desc",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClubListResponse:
    """Club supplier ranking — value_exported descending is the top-suppliers view."""
    page = queries.list_clubs(
        limit=limit, offset=offset, sort=sort, descending=order == "desc"
    )
    return ClubListResponse(
        items=[ClubMetricOut.from_record(c) for c in page.items],
        total=page.page.total,
        limit=page.page.limit,
        offset=page.page.offset,
        sort=sort,
        order=order,
    )


@router.get(
    "/nations/{nation_id}/supply-concentration",
    response_model=NationConcentrationResponse,
)
def get_nation_concentration(
    nation_id: int,
    queries: Annotated[GraphQueries, Depends(get_graph_queries)],
    top: Annotated[int, Query(ge=1, le=50)] = 10,
) -> NationConcentrationResponse:
    """A nation's HHI supply concentration + its top supplying clubs."""
    record = queries.get_nation_concentration(nation_id, top=top)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"no graph metrics for nation {nation_id} (unknown or not built)",
        )
    return NationConcentrationResponse.from_record(record)
