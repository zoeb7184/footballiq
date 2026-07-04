"""Grounded single-turn analyst pipeline (rag-design §§1, 6-7).

guardrails -> route -> grounded facts (SQL) + semantic retrieval -> templated
synthesis -> groundedness check -> cited, typed answer. No LLM: numbers come
from the FactProvider (executed SQL) and phrasing is a fixed template. The
LLMClient slots in later behind the same shape, with this as the fallback.
"""

from __future__ import annotations

from footballiq.application.rag.grounding import is_grounded
from footballiq.application.rag.ports import (
    AnalystAnswer,
    Citation,
    Fact,
    FactProvider,
    RetrievedChunk,
    Retriever,
)
from footballiq.application.rag.routing import classify

MAX_QUESTION_CHARS = 500
_CONTEXT_CHARS = 320
_REFUSAL = "The platform cannot answer that from its indexed docs and stored data."
_GUARDRAIL = "Question rejected: it must be non-empty and under 500 characters."
_VERSION_LABELS = frozenset(
    {"model_version", "feature_version", "scored_at", "graph_version"}
)


def _synthesize(facts: list[Fact], chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    if facts:
        parts.append("; ".join(f"{f.label}: {f.value}" for f in facts))
    if chunks:
        parts.append(f"Context: {chunks[0].content.strip()[:_CONTEXT_CHARS]}")
    return " -- ".join(parts)


class AnalystService:
    """Answers one question, grounded and cited. Stateless (single-turn)."""

    def __init__(
        self, *, facts: FactProvider, retriever: Retriever, k: int = 3
    ) -> None:
        self._facts = facts
        self._retriever = retriever
        self._k = k

    def ask(self, question: str) -> AnalystAnswer:
        q = question.strip()
        if not q or len(q) > MAX_QUESTION_CHARS:
            return AnalystAnswer(
                question=question, route="rejected", answer=_GUARDRAIL, grounded=True
            )
        route = classify(q)
        facts = self._facts.facts(route, q)
        chunks = self._retriever.retrieve(q, k=self._k)
        if not facts and not chunks:
            return AnalystAnswer(
                question=q, route=route.value, answer=_REFUSAL, grounded=True
            )
        answer = _synthesize(facts, chunks)
        return AnalystAnswer(
            question=q,
            route=route.value,
            answer=answer,
            grounded=is_grounded(answer, facts, chunks),
            facts=facts,
            citations=[Citation(c.source_path, c.section, c.score) for c in chunks],
            versions={f.label: f.value for f in facts if f.label in _VERSION_LABELS},
        )
