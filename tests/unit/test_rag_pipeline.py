"""Analyst pipeline tests (rag-design §§6-7) — fake fact provider + retriever."""

from footballiq.application.rag.pipeline import AnalystService
from footballiq.application.rag.ports import (
    Fact,
    QueryLogRecord,
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


class _Log:
    def __init__(self) -> None:
        self.records: list[QueryLogRecord] = []

    def record(self, entry: QueryLogRecord) -> None:
        self.records.append(entry)


class _LLM:
    def synthesize(
        self, question: str, facts: list[Fact], chunks: list[RetrievedChunk]  # noqa: ARG002
    ) -> str:
        return "phrased: " + "; ".join(f.value for f in facts)  # stays grounded


def _service(
    facts: list[Fact], chunks: list[RetrievedChunk],
    *, llm: object = None, log: object = None,
) -> AnalystService:
    return AnalystService(
        facts=_Facts(facts),
        retriever=_Retriever(chunks),
        llm=llm,  # type: ignore[arg-type]
        log=log,  # type: ignore[arg-type]
    )


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


def test_every_answer_is_audited() -> None:
    log = _Log()
    _service([Fact("Goals", "223", "gold.fact_match_event")], [], log=log).ask(
        "How many goals?")
    assert len(log.records) == 1
    rec = log.records[0]
    assert rec.route == "kpi" and rec.grounded is True and rec.fact_count == 1
    assert len(rec.response_hash) == 64  # sha256 hex


def test_llm_phrasing_is_used_and_grounding_rechecked() -> None:
    facts = [Fact("Goals", "223", "gold.fact_match_event")]
    ans = _service(facts, [], llm=_LLM()).ask("How many goals?")
    assert ans.answer.startswith("phrased:") and "223" in ans.answer
    assert ans.grounded is True
