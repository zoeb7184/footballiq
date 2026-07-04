"""Indexing orchestration tests (rag-design §5) — fake embedder + store.

No model download, no database: proves the content-hash diff (embed only what
changed), pruning of removed chunks, and idempotency.
"""

from footballiq.application.rag.indexing import index_documents
from footballiq.application.rag.ports import Chunk, EmbeddedChunk


class _FakeEmbedder:
    model_version = "fake-1"
    dim = 3

    def __init__(self) -> None:
        self.embedded: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embedded.extend(texts)
        return [[float(len(t)), 0.0, 1.0] for t in texts]


class _FakeStore:
    def __init__(self) -> None:
        self.data: dict[str, tuple[str, EmbeddedChunk]] = {}

    def existing_hashes(self) -> dict[str, str]:
        return {k: v[0] for k, v in self.data.items()}

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        for e in chunks:
            self.data[e.chunk.chunk_id] = (e.chunk.content_hash, e)

    def delete_missing(self, keep_ids: set[str]) -> int:
        gone = [k for k in self.data if k not in keep_ids]
        for k in gone:
            del self.data[k]
        return len(gone)


def _chunk(cid: str, content: str) -> Chunk:
    return Chunk(cid, "d.md", "doc", "S", content, content_hash=content)


def test_first_run_embeds_everything() -> None:
    emb, store = _FakeEmbedder(), _FakeStore()
    chunks = [_chunk("a", "alpha"), _chunk("b", "beta")]
    result = index_documents(chunks, embedder=emb, store=store)
    assert (result.total, result.embedded, result.skipped, result.pruned) == (2, 2, 0, 0)
    assert set(store.data) == {"a", "b"}


def test_unchanged_second_run_embeds_nothing() -> None:
    emb, store = _FakeEmbedder(), _FakeStore()
    chunks = [_chunk("a", "alpha"), _chunk("b", "beta")]
    index_documents(chunks, embedder=emb, store=store)
    emb.embedded.clear()
    result = index_documents(chunks, embedder=emb, store=store)
    assert result.embedded == 0 and result.skipped == 2
    assert emb.embedded == []  # nothing re-embedded


def test_changed_chunk_reembedded_only() -> None:
    emb, store = _FakeEmbedder(), _FakeStore()
    index_documents([_chunk("a", "alpha"), _chunk("b", "beta")],
                    embedder=emb, store=store)
    emb.embedded.clear()
    result = index_documents([_chunk("a", "alpha-v2"), _chunk("b", "beta")],
                             embedder=emb, store=store)
    assert result.embedded == 1 and emb.embedded == ["alpha-v2"]


def test_removed_chunks_pruned() -> None:
    emb, store = _FakeEmbedder(), _FakeStore()
    index_documents([_chunk("a", "alpha"), _chunk("b", "beta")],
                    embedder=emb, store=store)
    result = index_documents([_chunk("a", "alpha")], embedder=emb, store=store)
    assert result.pruned == 1 and set(store.data) == {"a"}
