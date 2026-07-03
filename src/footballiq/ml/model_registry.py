"""Lightweight model registry (ML design v1.1 §10) — a table we fully own.

Entries carry complete lineage: feature_version pin, git commit, params,
seed, metrics. Promotion is a recorded status change; 'what served on date
X' is always answerable.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, text


@dataclass(frozen=True, slots=True)
class ProductionModel:
    """The lineage a scoring run needs to load and pin the served model."""

    model_id: str
    version: str
    feature_version: str
    artifact_path: str

_DDL = """
CREATE TABLE IF NOT EXISTS {p}model_registry (
    model_id        TEXT PRIMARY KEY,
    task            TEXT NOT NULL,
    version         TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    git_commit      TEXT NOT NULL,
    params          TEXT NOT NULL,
    metrics         TEXT NOT NULL,
    seed            INTEGER NOT NULL,
    artifact_path   TEXT NOT NULL,
    status          TEXT NOT NULL,
    created_at      TEXT NOT NULL
)
"""


def current_git_commit() -> str:
    try:
        out = subprocess.run(  # fixed argv, no user input
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        return out.stdout.strip()
    except Exception:  # pragma: no cover - environment-dependent
        return "unknown"


def register_production_model(  # noqa: PLR0913 - full lineage is the point
    engine: Engine,
    *,
    task: str,
    version: str,
    feature_version: str,
    params: dict[str, object],
    metrics: dict[str, dict[str, float]],
    seed: int,
    artifact_path: str,
    schema: str | None = "gold",
) -> str:
    """Register a gate-passing model and promote it (demoting predecessors)."""
    p = f"{schema}." if schema else ""
    model_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(text(_DDL.format(p=p)))
        conn.execute(
            text(
                f"UPDATE {p}model_registry SET status = 'archived' "
                "WHERE task = :task AND status = 'production'"
            ),
            {"task": task},
        )
        conn.execute(
            text(
                f"INSERT INTO {p}model_registry VALUES "
                "(:id, :task, :version, :fversion, :commit, :params, :metrics, "
                ":seed, :artifact, 'production', :ts)"
            ),
            {
                "id": model_id,
                "task": task,
                "version": version,
                "fversion": feature_version,
                "commit": current_git_commit(),
                "params": json.dumps(params),
                "metrics": json.dumps(metrics),
                "seed": seed,
                "artifact": artifact_path,
                "ts": datetime.now(tz=UTC).isoformat(),
            },
        )
    return model_id


class NoProductionModel(RuntimeError):
    """No model is in production for the requested task — score run cannot start."""


def load_production_model(
    engine: Engine, *, task: str, schema: str | None = "gold"
) -> ProductionModel:
    """The single production model for a task; its version + feature_version pin
    every prediction and explanation written against it."""
    p = f"{schema}." if schema else ""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                f"SELECT model_id, version, feature_version, artifact_path "
                f"FROM {p}model_registry "
                "WHERE task = :task AND status = 'production'"
            ),
            {"task": task},
        ).one_or_none()
    if row is None:
        msg = f"no production model for task {task!r} — run `make train` first"
        raise NoProductionModel(msg)
    return ProductionModel(
        model_id=str(row[0]),
        version=str(row[1]),
        feature_version=str(row[2]),
        artifact_path=str(row[3]),
    )
