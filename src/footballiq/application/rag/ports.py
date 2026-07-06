"""RAG ports and DTOs (rag-design §§1, 4-5).

Records are plain application-level results; infrastructure adapters implement
the ports. Keeping these here lets the chunker and indexer stay pure and fully
unit-testable with fakes — no model download, no database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Chunk:
    """One heading-aware slice of a source document, pre-embedding."""

    chunk_id: str        # deterministic: source_path + section + ordinal
    source_path: str
    source_type: str     # doc | adr | module_report | kpi | ...
    section: str         # heading trail, e.g. "ML System Design > 2. Feature design"
    content: str
    content_hash: str    # sha256 of content — drives incremental re-index


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    """A chunk with its embedding vector, ready to persist."""

    chunk: Chunk
    embedding: list[float]
    embed_model_version: str


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A semantic-search hit (cosine similarity in [0, 1], higher = closer)."""

    chunk_id: str
    content: str
    source_path: str
    section: str
    score: float


class Embedder(Protocol):
    """Turns text into vectors. Same model embeds documents and queries."""

    @property
    def model_version(self) -> str: ...

    @property
    def dim(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class ChunkStore(Protocol):
    """Persistence + semantic search over the vector store (ai.document_chunk)."""

    def existing_hashes(self) -> dict[str, str]: ...

    def upsert(self, chunks: list[EmbeddedChunk]) -> None: ...

    def delete_missing(self, keep_ids: set[str]) -> int: ...

    def search(self, embedding: list[float], *, k: int) -> list[RetrievedChunk]: ...


class Route(StrEnum):
    """Where a question is routed (rag-design §1). DOCS = retrieval-only."""

    KPI = "kpi"
    PREDICTION = "prediction"
    EXPLANATION = "explanation"
    GRAPH = "graph"
    DOCS = "docs"


@dataclass(frozen=True, slots=True)
class Fact:
    """One grounded numeric fact from executed SQL — never from the LLM."""

    label: str
    value: str      # rendered exactly as it must appear in the answer
    source: str     # e.g. "gold.prediction_player_valuation"
    kind: str = "fact"  # fact | prediction | explanation | graph


@dataclass(frozen=True, slots=True)
class Citation:
    """A retrieved document reference backing a definitional claim."""

    source_path: str
    section: str
    score: float


@dataclass(frozen=True, slots=True)
class AnalystAnswer:
    """A typed, cited, grounded answer (rag-design §7)."""

    question: str
    route: str
    answer: str
    grounded: bool
    facts: list[Fact] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    versions: dict[str, str] = field(default_factory=dict)


class FactProvider(Protocol):
    """Executes the SQL catalog for a route; returns grounded numeric facts."""

    def facts(self, route: Route, question: str) -> list[Fact]: ...


class Retriever(Protocol):
    """Embeds a question and returns the closest document chunks."""

    def retrieve(self, question: str, *, k: int) -> list[RetrievedChunk]: ...


class LLMClient(Protocol):
    """Phrases a grounded answer from facts + retrieved context (rag-design §6).

    The LLM may only use the supplied tool content; the pipeline re-checks
    groundedness on whatever it returns. The default is a deterministic template
    (no key required); a hosted model slots in behind this same shape.
    """

    def synthesize(
        self, question: str, facts: list[Fact], chunks: list[RetrievedChunk]
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class QueryLogRecord:
    """One audit row — every answer must be reconstructible (rag-design §8)."""

    question: str
    route: str
    grounded: bool
    fact_count: int
    citation_count: int
    response_hash: str
    versions: dict[str, str]


class QueryLog(Protocol):
    """Append-only audit sink for analyst answers (ai.query_log)."""

    def record(self, entry: QueryLogRecord) -> None: ...
