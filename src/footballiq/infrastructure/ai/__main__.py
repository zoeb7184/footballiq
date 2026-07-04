"""RAG indexing CLI: `python -m footballiq.infrastructure.ai index [docs_dir]`.

Walks the docs tree, chunks each Markdown file heading-aware, and (re)indexes
changed chunks into ai.document_chunk. Composition root for the batch job: wires
the sentence-transformers embedder and pgvector store to the pure indexer.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine

from footballiq.application.rag.chunking import chunk_markdown
from footballiq.application.rag.indexing import index_documents
from footballiq.application.rag.ports import Chunk
from footballiq.infrastructure.ai.embeddings import SentenceTransformerEmbedder
from footballiq.infrastructure.ai.vector_store import PgVectorChunkStore
from footballiq.infrastructure.config import load_settings


def _source_type(path: str) -> str:
    lower = path.lower()
    if "modules" in lower:
        return "module_report"
    if "adr" in lower:
        return "adr"
    return "doc"


def _collect(docs_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.rglob("*.md")):
        rel = str(path)
        chunks.extend(chunk_markdown(rel, _source_type(rel), path.read_text("utf-8")))
    return chunks


def main(args: list[str]) -> int:
    if args and args[0] == "index":
        docs_dir = Path(args[1]) if len(args) > 1 else Path("docs")
        chunks = _collect(docs_dir)
        engine = create_engine(load_settings().database_url)
        store = PgVectorChunkStore(engine)
        store.ensure_table()
        result = index_documents(
            chunks, embedder=SentenceTransformerEmbedder(), store=store
        )
        print(
            f"ai.document_chunk: {result.total} chunks "
            f"({result.embedded} embedded, {result.skipped} unchanged, "
            f"{result.pruned} pruned)"
        )
        return 0
    print("usage: python -m footballiq.infrastructure.ai index [docs_dir]")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
