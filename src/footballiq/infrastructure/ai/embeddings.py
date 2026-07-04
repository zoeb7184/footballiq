"""Local sentence-transformers embedder (rag-design §5).

bge-small-en-v1.5 class: free, local, CPU-friendly, 384-dim. The model loads
lazily on first embed so importing this module (and running the rest of the
suite) never pulls the heavy dependency. Unit tests use a fake Embedder.
"""

from __future__ import annotations

from typing import Any

_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_MODEL_VERSION = "bge-small-en-v1.5"
_DIM = 384


class SentenceTransformerEmbedder:
    """Embedder port backed by sentence-transformers (loaded on first use)."""

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: Any = None

    @property
    def model_version(self) -> str:
        return _MODEL_VERSION

    @property
    def dim(self) -> int:
        return _DIM

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        # normalize_embeddings=True -> cosine == dot product; matches the store.
        vectors = model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return [[float(x) for x in row] for row in vectors]
