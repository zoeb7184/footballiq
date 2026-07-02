"""Bronze loader — verbatim CSV landing with load registry.

Engine-agnostic (SQLAlchemy Core + text SQL); schema prefix is configurable
so unit tests can run on SQLite while production targets Postgres `bronze`.
"""

from __future__ import annotations

import csv
import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine, text

from footballiq.infrastructure.ingestion.manifest import Source

_REGISTRY = "_loads"


@dataclass(frozen=True, slots=True)
class LoadResult:
    """Outcome of one source ingestion."""

    source_file: str
    load_id: str
    rows: int
    skipped: bool  # True when unchanged file was already loaded (no-op)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quote(identifier: str) -> str:
    """Quote an identifier from the trusted manifest (defense in depth)."""
    if not identifier.replace("_", "").isalnum():
        msg = f"unsafe identifier: {identifier!r}"
        raise ValueError(msg)
    return f'"{identifier}"'


class BronzeLoader:
    """Loads declared sources into the bronze layer, append-only."""

    def __init__(self, engine: Engine, *, schema: str | None = "bronze") -> None:
        self._engine = engine
        self._prefix = f"{_quote(schema)}." if schema else ""

    def _ensure_registry(self) -> None:
        ddl = (
            f"CREATE TABLE IF NOT EXISTS {self._prefix}{_quote(_REGISTRY)} ("
            "load_id TEXT PRIMARY KEY, source_file TEXT NOT NULL, "
            "file_sha256 TEXT NOT NULL, row_count INTEGER NOT NULL, "
            "ingested_at TEXT NOT NULL)"
        )
        with self._engine.begin() as conn:
            conn.execute(text(ddl))

    def _already_loaded(self, source_file: str, sha: str) -> bool:
        query = text(
            f"SELECT 1 FROM {self._prefix}{_quote(_REGISTRY)} "
            "WHERE source_file = :f AND file_sha256 = :s LIMIT 1"
        )
        with self._engine.connect() as conn:
            return conn.execute(query, {"f": source_file, "s": sha}).first() is not None

    def load(self, source: Source, data_dir: Path) -> LoadResult:
        """Ingest one source file. Unchanged files are a recorded no-op."""
        path = data_dir / source.filename
        sha = _sha256(path)
        self._ensure_registry()
        if self._already_loaded(source.filename, sha):
            return LoadResult(source.filename, load_id="", rows=0, skipped=True)

        load_id = str(uuid.uuid4())
        ingested_at = datetime.now(tz=UTC).isoformat()
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                msg = f"{source.filename}: empty file"
                raise ValueError(msg)
            fieldnames = list(reader.fieldnames)
            columns = [c.strip() for c in fieldnames]
            rows = [dict(r) for r in reader]

        table = f"{self._prefix}{_quote(source.bronze_table)}"
        col_ddl = ", ".join(f"{_quote(c)} TEXT" for c in columns)
        meta_ddl = (
            "_load_id TEXT NOT NULL, _source_file TEXT NOT NULL, "
            "_file_sha256 TEXT NOT NULL, _ingested_at TEXT NOT NULL"
        )
        insert_cols = ", ".join(_quote(c) for c in columns)
        params = ", ".join(f":{i}" for i in range(len(columns)))
        insert = text(
            f"INSERT INTO {table} ({insert_cols}, _load_id, _source_file, "
            f"_file_sha256, _ingested_at) VALUES ({params}, :lid, :sf, :sha, :ts)"
        )
        register = text(
            f"INSERT INTO {self._prefix}{_quote(_REGISTRY)} VALUES (:lid, :sf, :sha, :n, :ts)"
        )
        stamp: dict[str, str] = {
            "lid": load_id, "sf": source.filename, "sha": sha, "ts": ingested_at,
        }
        with self._engine.begin() as conn:
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table} ({col_ddl}, {meta_ddl})"))
            for row in rows:
                values: dict[str, str | None] = {
                    str(i): row.get(orig) for i, orig in enumerate(fieldnames)
                }
                values.update(stamp)
                conn.execute(insert, values)
            conn.execute(register, {**stamp, "n": len(rows)})
        return LoadResult(source.filename, load_id=load_id, rows=len(rows), skipped=False)
