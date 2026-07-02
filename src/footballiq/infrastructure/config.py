"""Runtime configuration — the ONLY module that reads the environment.

ADR-0003: all environment access goes through here so the config provider
can be swapped (env files locally, Key Vault on Azure) without touching
consumers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_DB_URL = "postgresql+psycopg://fiq:fiq_local_dev@localhost:5432/footballiq"


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings."""

    database_url: str
    data_dir: Path


def load_settings() -> Settings:
    """Build settings from environment with local-dev defaults."""
    return Settings(
        database_url=os.environ.get("FIQ_DATABASE_URL", _DEFAULT_DB_URL),
        data_dir=Path(os.environ.get("FIQ_DATA_DIR", "data/raw")),
    )
