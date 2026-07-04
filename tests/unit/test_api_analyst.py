"""Analyst endpoint tests — fake service (rag-design §1)."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from footballiq.api.main import create_app
from footballiq.application.rag.ports import AnalystAnswer, Citation, Fact
from footballiq.infrastructure.config import Settings

_KEY = "test-key"
_AUTH = {"X-API-Key": _KEY}


class _FakeAnalyst:
    def ask(self, question: str) -> AnalystAnswer:
        return AnalystAnswer(
            question=question, route="kpi",
            answer="Total squad value (EUR): 17140000000",
            grounded=True,
            facts=[Fact("Total squad value (EUR)", "17140000000", "gold.dim_player")],
            citations=[Citation("docs/kpi.md", "KPI", 0.9)],
            versions={},
        )


def _client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        data_dir=Path("data/raw"),
        api_key_hashes=(hashlib.sha256(_KEY.encode()).hexdigest(),),
    )
    app = create_app(settings)
    app.state.analyst_service = _FakeAnalyst()
    return TestClient(app, raise_server_exceptions=False)


def test_ask_returns_grounded_cited_answer() -> None:
    resp = _client().post(
        "/v1/analyst/ask", json={"question": "total squad value?"}, headers=_AUTH
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is True
    assert body["route"] == "kpi"
    assert "17140000000" in body["answer"]
    assert body["facts"][0]["source"] == "gold.dim_player"
    assert body["citations"][0]["source_path"] == "docs/kpi.md"


def test_empty_question_rejected_and_auth() -> None:
    assert _client().post(
        "/v1/analyst/ask", json={"question": ""}, headers=_AUTH
    ).status_code == 422
    assert _client().post(
        "/v1/analyst/ask", json={"question": "hi"}
    ).status_code == 401
