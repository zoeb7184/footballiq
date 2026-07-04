"""pgvector-backed chunk store (rag-design §4).

Persists embeddings in ai.document_chunk and does exact cosine search via the
pgvector `<=>` operator (HNSW is a documented scale flip-on). Embeddings are
sent as vector literals and cast in SQL, so no extra client library is needed.
The ai schema, `vector` extension, and fiq_analyst role are provisioned by the
init SQL / `make ai-up`; this adapter only manages the table.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Engine, bindparam, text

from footballiq.application.rag.ports import EmbeddedChunk, RetrievedChunk

_DIM = 384

_DDL = """
CREATE TABLE IF NOT EXISTS {s}.document_chunk (
    chunk_id            TEXT PRIMARY KEY,
    content             TEXT NOT NULL,
    embedding           vector({dim}) NOT NULL,
    source_path         TEXT NOT NULL,
    source_type         TEXT NOT NULL,
    section             TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    embed_model_version TEXT NOT NULL,
    indexed_at          TEXT NOT NULL
)
"""


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


class PgVectorChunkStore:
    """ChunkStore port over ai.document_chunk (Postgres + pgvector)."""

    def __init__(self, engine: Engine, *, schema: str = "ai") -> None:
        self._engine = engine
        self._schema = schema
        with engine.begin() as conn:
            conn.execute(text(_DDL.format(s=schema, dim=_DIM)))

    def existing_hashes(self) -> dict[str, str]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(f"SELECT chunk_id, content_hash FROM {self._schema}.document_chunk")
            ).all()
        return {str(r[0]): str(r[1]) for r in rows}

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        if not chunks:
            return
        stmt = text(
            f"INSERT INTO {self._schema}.document_chunk (chunk_id, content, "
            "embedding, source_path, source_type, section, content_hash, "
            "embed_model_version, indexed_at) VALUES "
            "(:chunk_id, :content, CAST(:embedding AS vector), :source_path, "
            ":source_type, :section, :content_hash, :embed_model_version, :indexed_at) "
            "ON CONFLICT (chunk_id) DO UPDATE SET "
            "content = EXCLUDED.content, embedding = EXCLUDED.embedding, "
            "section = EXCLUDED.section, content_hash = EXCLUDED.content_hash, "
            "embed_model_version = EXCLUDED.embed_model_version, "
            "indexed_at = EXCLUDED.indexed_at"
        )
        now = datetime.now(tz=UTC).isoformat()
        params = [
            {
                "chunk_id": e.chunk.chunk_id,
                "content": e.chunk.content,
                "embedding": _vector_literal(e.embedding),
                "source_path": e.chunk.source_path,
                "source_type": e.chunk.source_type,
                "section": e.chunk.section,
                "content_hash": e.chunk.content_hash,
                "embed_model_version": e.embed_model_version,
                "indexed_at": now,
            }
            for e in chunks
        ]
        with self._engine.begin() as conn:
            conn.execute(stmt, params)

    def delete_missing(self, keep_ids: set[str]) -> int:
        with self._engine.begin() as conn:
            if not keep_ids:
                result = conn.execute(
                    text(f"DELETE FROM {self._schema}.document_chunk")
                )
                return int(result.rowcount)
            stmt = text(
                f"DELETE FROM {self._schema}.document_chunk WHERE chunk_id NOT IN :ids"
            ).bindparams(bindparam("ids", expanding=True))
            result = conn.execute(stmt, {"ids": list(keep_ids)})
        return int(result.rowcount)

    def search(self, embedding: list[float], *, k: int) -> list[RetrievedChunk]:
        stmt = text(
            "SELECT chunk_id, content, source_path, section, "
            "1 - (embedding <=> CAST(:q AS vector)) AS score "
            f"FROM {self._schema}.document_chunk "
            "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(
                stmt, {"q": _vector_literal(embedding), "k": k}
            ).all()
        return [
            RetrievedChunk(
                chunk_id=str(r[0]), content=str(r[1]), source_path=str(r[2]),
                section=str(r[3]), score=float(r[4]),
            )
            for r in rows
        ]
