"""Incremental indexing orchestration (rag-design §5).

Embeds only chunks whose content changed since the last run (content-hash diff)
and prunes chunks whose source no longer produces them. Pure orchestration over
the Embedder and ChunkStore ports — no model, no DB here.
"""

from __future__ import annotations

from dataclasses import dataclass

from footballiq.application.rag.ports import (
    Chunk,
    ChunkStore,
    EmbeddedChunk,
    Embedder,
)


@dataclass(frozen=True, slots=True)
class IndexResult:
    """What an indexing run changed."""

    total: int
    embedded: int
    skipped: int
    pruned: int


def index_documents(
    chunks: list[Chunk], *, embedder: Embedder, store: ChunkStore
) -> IndexResult:
    """(Re)index chunks: embed changed content, upsert, prune removed."""
    existing = store.existing_hashes()
    to_embed = [c for c in chunks if existing.get(c.chunk_id) != c.content_hash]
    if to_embed:
        vectors = embedder.embed([c.content for c in to_embed])
        store.upsert([
            EmbeddedChunk(
                chunk=c, embedding=v, embed_model_version=embedder.model_version
            )
            for c, v in zip(to_embed, vectors, strict=True)
        ])
    pruned = store.delete_missing({c.chunk_id for c in chunks})
    return IndexResult(
        total=len(chunks),
        embedded=len(to_embed),
        skipped=len(chunks) - len(to_embed),
        pruned=pruned,
    )
