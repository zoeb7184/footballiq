"""RAG ports and DTOs (rag-design §§1, 4-5).

Records are plain application-level results; infrastructure adapters implement
the ports. Keeping these here lets the chunker and indexer stay pure and fully
unit-testable with fakes — no model download, no database.
"""

from __future__ import annotations

from dataclasses import dataclass
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
