"""FastAPI application factory — the composition root (ARB L2 decision).

The api layer is outermost (ADR-0002) and wires settings → engine →
adapters at startup. Nothing below this module knows concrete adapters.

Run locally:  uvicorn footballiq.api.main:create_app --factory --reload
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine

import footballiq
from footballiq.api.auth import require_api_key
from footballiq.api.errors import register_error_handlers
from footballiq.api.routers.system import router as system_router
from footballiq.api.routers.teams import router as teams_router
from footballiq.application.queries import TeamQueries
from footballiq.infrastructure.config import Settings, load_settings
from footballiq.infrastructure.gold.readiness import GoldReadinessProbe
from footballiq.infrastructure.gold.teams import GoldTeamReadModel


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application with all dependencies wired."""
    settings = settings or load_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    app = FastAPI(
        title="FootballIQ Enterprise API",
        version=footballiq.__version__,
        description=(
            "Read-only decision-intelligence API over the gold layer. "
            "Prediction-as-data: no model runs at request time."
        ),
    )
    app.state.settings = settings
    app.state.probe = GoldReadinessProbe(engine)
    app.state.team_queries = TeamQueries(GoldTeamReadModel(engine))

    register_error_handlers(app)
    app.include_router(system_router)  # unauthenticated: probes must reach it
    app.include_router(teams_router, dependencies=[Depends(require_api_key)])
    return app
