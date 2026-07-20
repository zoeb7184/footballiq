"""Simulation endpoint: POST /v1/simulations/match (ADR-0006).

Monte Carlo over warehouse Elo ratings and the observed scoring rate.
Deterministic per seed; the response carries its own assumptions so the
client can render the methodology next to the numbers.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from footballiq.api.schemas import SimulateMatchRequest, SimulationResponse
from footballiq.application.simulation import (
    MissingRatingError,
    SimulationService,
    UnknownTeamError,
)

router = APIRouter(prefix="/v1/simulations", tags=["simulations"])


def get_simulation_service(request: Request) -> SimulationService:
    service: SimulationService = request.app.state.simulation_service
    return service


@router.post("/match", response_model=SimulationResponse)
def simulate_match(
    body: SimulateMatchRequest,
    service: Annotated[SimulationService, Depends(get_simulation_service)],
) -> SimulationResponse:
    """Simulate one fixture n_runs times; identical inputs+seed ⇒ identical output."""
    try:
        result = service.simulate_match(
            home_team_id=body.home_team_id,
            away_team_id=body.away_team_id,
            n_runs=body.n_runs,
            seed=body.seed,
        )
    except UnknownTeamError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MissingRatingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SimulationResponse.from_result(result)
