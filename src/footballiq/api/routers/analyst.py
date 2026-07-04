"""Analyst (RAG) endpoint: POST /v1/analyst/ask (rag-design §1).

Single-turn, grounded, cited. Numbers come from executed SQL; retrieval adds
definitional context. Same API-key auth as the rest of the platform.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from footballiq.api.schemas import AnalystResponse, AskRequest
from footballiq.application.rag.pipeline import AnalystService

router = APIRouter(prefix="/v1/analyst", tags=["analyst"])


def get_analyst(request: Request) -> AnalystService:
    service: AnalystService = request.app.state.analyst_service
    return service


@router.post("/ask", response_model=AnalystResponse)
def ask(
    body: AskRequest,
    service: Annotated[AnalystService, Depends(get_analyst)],
) -> AnalystResponse:
    """Answer one question from stored data + indexed docs, grounded and cited."""
    return AnalystResponse.from_answer(service.ask(body.question))
