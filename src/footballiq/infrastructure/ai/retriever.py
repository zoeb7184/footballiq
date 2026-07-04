"""Semantic retriever (rag-design §2): embed the question, search the store.

Thin composition of the Embedder and ChunkStore ports into the Retriever the
pipeline consumes. The heavy model loads lazily inside the embedder, so
constructing this is cheap (safe to wire at API startup).
"""

from __future__ import annotations

from footballiq.application.rag.ports import ChunkStore, Embedder, RetrievedChunk


class SemanticRetriever:
    """Retriever port backed by a local embedder + pgvector store."""

    def __init__(self, embedder: Embedder, store: ChunkStore) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, question: str, *, k: int) -> list[RetrievedChunk]:
        vector = self._embedder.embed([question])[0]
        return self._store.search(vector, k=k)
