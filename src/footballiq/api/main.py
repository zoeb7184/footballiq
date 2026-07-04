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
from footballiq.api.routers.analyst import router as analyst_router
from footballiq.api.routers.graph import router as graph_router
from footballiq.api.routers.matches import router as matches_router
from footballiq.api.routers.players import router as players_router
from footballiq.api.routers.system import router as system_router
from footballiq.api.routers.teams import router as teams_router
from footballiq.api.routers.valuations import router as valuations_router
from footballiq.application.queries import (
    GraphQueries,
    MatchQueries,
    PlayerQueries,
    TeamQueries,
    ValuationQueries,
)
from footballiq.application.rag.pipeline import AnalystService
from footballiq.infrastructure.ai.embeddings import SentenceTransformerEmbedder
from footballiq.infrastructure.ai.fact_provider import GoldFactProvider
from footballiq.infrastructure.ai.retriever import SemanticRetriever
from footballiq.infrastructure.ai.vector_store import PgVectorChunkStore
from footballiq.infrastructure.config import Settings, load_settings
from footballiq.infrastructure.gold.graph import GoldGraphReadModel
from footballiq.infrastructure.gold.matches import GoldMatchReadModel
from footballiq.infrastructure.gold.players import GoldPlayerReadModel
from footballiq.infrastructure.gold.readiness import GoldReadinessProbe
from footballiq.infrastructure.gold.teams import GoldTeamReadModel
from footballiq.infrastructure.gold.valuations import GoldValuationReadModel


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
    app.state.match_queries = MatchQueries(GoldMatchReadModel(engine))
    app.state.player_queries = PlayerQueries(GoldPlayerReadModel(engine))
    app.state.valuation_queries = ValuationQueries(GoldValuationReadModel(engine))
    app.state.graph_queries = GraphQueries(GoldGraphReadModel(engine))
    app.state.analyst_service = AnalystService(
        facts=GoldFactProvider(engine),
        retriever=SemanticRetriever(
            SentenceTransformerEmbedder(), PgVectorChunkStore(engine)
        ),
    )

    register_error_handlers(app)
    app.include_router(system_router)  # unauthenticated: probes must reach it
    app.include_router(teams_router, dependencies=[Depends(require_api_key)])
    app.include_router(matches_router, dependencies=[Depends(require_api_key)])
    app.include_router(players_router, dependencies=[Depends(require_api_key)])
    app.include_router(valuations_router, dependencies=[Depends(require_api_key)])
    app.include_router(graph_router, dependencies=[Depends(require_api_key)])
    app.include_router(analyst_router, dependencies=[Depends(require_api_key)])
    return app
