"""Runtime configuration — the ONLY module that reads the environment.

ADR-0003: all environment access goes through here so the config provider
can be swapped (env files locally, Key Vault on Azure) without touching
consumers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_DB_URL = "postgresql+psycopg://fiq:fiq_local_dev@localhost:5432/footballiq"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (ARB finding M1b): KEY=VALUE lines, never
    overriding variables already set in the real environment."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings."""

    database_url: str
    data_dir: Path
    api_key_hashes: tuple[str, ...] = field(default=())
    # Least-privilege engine for the RAG analyst's reads (fiq_analyst: SELECT on
    # gold + ai only). Defaults to database_url so local dev works unconfigured.
    analyst_database_url: str | None = None

    @property
    def analyst_url(self) -> str:
        return self.analyst_database_url or self.database_url


def load_settings(dotenv_path: Path = Path(".env")) -> Settings:
    """Build settings from environment (+ optional .env) with local defaults."""
    _load_dotenv(dotenv_path)
    raw_hashes = os.environ.get("FIQ_API_KEY_HASHES", "")
    return Settings(
        database_url=os.environ.get("FIQ_DATABASE_URL", _DEFAULT_DB_URL),
        data_dir=Path(os.environ.get("FIQ_DATA_DIR", "data/raw")),
        api_key_hashes=tuple(h.strip() for h in raw_hashes.split(",") if h.strip()),
        analyst_database_url=os.environ.get("FIQ_ANALYST_DATABASE_URL"),
    )
