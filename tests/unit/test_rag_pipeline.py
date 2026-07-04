"""Analyst pipeline tests (rag-design §§6-7) — fake fact provider + retriever."""

from footballiq.application.rag.pipeline import AnalystService
from footballiq.application.rag.ports import (
    Fact,
    RetrievedChunk,
    Route,
)


class _Facts:
    def __init__(self, facts: list[Fact]) -> None:
        self._facts = facts

    def facts(self, route: Route, question: str) -> list[Fact]:  # noqa: ARG002
        return self._facts


class _Retriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    def retrieve(self, question: str, *, k: int) -> list[RetrievedChunk]:  # noqa: ARG002
        return self._chunks


def _service(facts: list[Fact], chunks: list[RetrievedChunk]) -> AnalystService:
    return AnalystService(facts=_Facts(facts), retriever=_Retriever(chunks))


def test_grounded_answer_carries_facts_and_citations() -> None:
    facts = [Fact("Total squad value (EUR)", "17140000000", "gold.dim_player"),
             Fact("model_version", "1.0.0", "gold.prediction", "prediction")]
    chunks = [RetrievedChunk("id", "Squad value is the sum of market values.",
                             "docs/kpi.md", "KPI", 0.88)]
    ans = _service(facts, chunks).ask("What is the total squad value?")
    assert ans.grounded is True
    assert "17140000000" in ans.answer
    assert [c.source_path for c in ans.citations] == ["docs/kpi.md"]
    assert ans.versions == {"model_version": "1.0.0"}


def test_empty_evidence_refuses() -> None:
    ans = _service([], []).ask("Who will win the Ballon d'Or in 2030?")
    assert "cannot answer" in ans.answer.lower()
    assert ans.facts == [] and ans.grounded is True


def test_guardrail_rejects_empty_and_overlong() -> None:
    svc = _service([Fact("x", "1", "s")], [])
    assert svc.ask("   ").route == "rejected"
    assert svc.ask("q" * 501).route == "rejected"
