"""FastAPI application factory — the composition root (ARB L2 decision).

The api layer is outermost (ADR-0002) and wires settings → engine →
adapters at startup. Nothing below this module knows concrete adapters.

Run locally:  uvicorn footballiq.api.main:create_app --factory --reload
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

import footballiq
from footballiq.api.auth import require_api_key
from footballiq.api.errors import register_error_handlers
from footballiq.api.routers.analyst import router as analyst_router
from footballiq.api.routers.graph import router as graph_router
from footballiq.api.routers.matches import router as matches_router
from footballiq.api.routers.models import router as models_router
from footballiq.api.routers.players import router as players_router
from footballiq.api.routers.simulations import router as simulations_router
from footballiq.api.routers.system import router as system_router
from footballiq.api.routers.teams import router as teams_router
from footballiq.api.routers.valuations import router as valuations_router
from footballiq.application.model_performance import ModelPerformanceQueries
from footballiq.application.queries import (
    GraphQueries,
    MatchQueries,
    PlayerQueries,
    TeamQueries,
    ValuationQueries,
)
from footballiq.application.rag.pipeline import AnalystService
from footballiq.application.simulation import SimulationService
from footballiq.infrastructure.ai.embeddings import SentenceTransformerEmbedder
from footballiq.infrastructure.ai.fact_provider import GoldFactProvider
from footballiq.infrastructure.ai.query_log import PgQueryLog
from footballiq.infrastructure.ai.retriever import SemanticRetriever
from footballiq.infrastructure.ai.vector_store import PgVectorChunkStore
from footballiq.infrastructure.config import Settings, load_settings
from footballiq.infrastructure.gold.graph import GoldGraphReadModel
from footballiq.infrastructure.gold.matches import GoldMatchReadModel
from footballiq.infrastructure.gold.model_performance import GoldModelPerformanceReadModel
from footballiq.infrastructure.gold.players import GoldPlayerReadModel
from footballiq.infrastructure.gold.readiness import GoldReadinessProbe
from footballiq.infrastructure.gold.simulation import GoldScoringRateReadModel
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
    app.state.simulation_service = SimulationService(
        GoldTeamReadModel(engine), GoldScoringRateReadModel(engine)
    )
    app.state.model_performance_queries = ModelPerformanceQueries(
        GoldModelPerformanceReadModel(engine)
    )
    # Analyst reads through a least-privilege engine (fiq_analyst: gold + ai
    # only); audit writes go through the app-owner engine.
    analyst_engine = create_engine(settings.analyst_url, pool_pre_ping=True)
    app.state.analyst_service = AnalystService(
        facts=GoldFactProvider(analyst_engine),
        retriever=SemanticRetriever(
            SentenceTransformerEmbedder(), PgVectorChunkStore(analyst_engine)
        ),
        log=PgQueryLog(engine),
    )

    if settings.cors_origins:
        # Opt-in via FIQ_CORS_ORIGINS: browser clients (e.g. Swagger from a
        # docs host) — the production web app calls through its own server-side
        # proxy and never needs CORS.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["X-API-Key", "Content-Type"],
        )

    register_error_handlers(app)
    app.include_router(system_router)  # unauthenticated: probes must reach it
    app.include_router(teams_router, dependencies=[Depends(require_api_key)])
    app.include_router(matches_router, dependencies=[Depends(require_api_key)])
    app.include_router(players_router, dependencies=[Depends(require_api_key)])
    app.include_router(valuations_router, dependencies=[Depends(require_api_key)])
    app.include_router(graph_router, dependencies=[Depends(require_api_key)])
    app.include_router(analyst_router, dependencies=[Depends(require_api_key)])
    app.include_router(simulations_router, dependencies=[Depends(require_api_key)])
    app.include_router(models_router, dependencies=[Depends(require_api_key)])
    return app
