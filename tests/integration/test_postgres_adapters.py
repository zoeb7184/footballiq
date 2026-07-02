"""Ring-2 integration tests against real Postgres (ARB H1).

Run locally with the compose warehouse or in CI's service container:
    FIQ_TEST_DATABASE_URL=postgresql+psycopg://fiq:fiq_local_dev@localhost:5432/footballiq
Skipped entirely when the variable is absent.
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from footballiq.infrastructure.gold.teams import GoldTeamReadModel
from footballiq.infrastructure.ingestion.bronze import BronzeLoader
from footballiq.infrastructure.ingestion.manifest import Source

_URL = os.environ.get("FIQ_TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(_URL is None, reason="FIQ_TEST_DATABASE_URL not set"),
]

_SCHEMA = "it_gold"  # isolated schemas: never touch real bronze/gold
_BRONZE = "it_bronze"


def _engine():  # type: ignore[no-untyped-def]
    return create_engine(str(_URL))


def test_team_read_model_excludes_reserved_members_on_postgres() -> None:
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {_SCHEMA}"))
        conn.execute(
            text(
                f"CREATE TABLE {_SCHEMA}.dim_team (team_sk int, team_id_nat int, "
                "team_name text, fifa_code text, group_letter text, confederation text, "
                "fifa_ranking int, elo_rating int, manager_name text)"
            )
        )
        conn.execute(
            text(
                f"INSERT INTO {_SCHEMA}.dim_team VALUES "
                "(1, 1, 'Mexico', 'MEX', 'A', 'CONCACAF', 14, 1810, 'X'), "
                "(2, 2, 'Canada', 'CAN', 'B', 'CONCACAF', 40, 1700, 'Y'), "
                "(-1, NULL, 'Unknown', 'UNK', NULL, NULL, NULL, NULL, NULL), "
                "(-2, NULL, 'To Be Determined', 'TBD', NULL, NULL, NULL, NULL, NULL)"
            )
        )
    rm = GoldTeamReadModel(engine, schema=_SCHEMA)

    assert rm.count_teams() == 2  # reserved members invisible
    names = [t.name for t in rm.list_teams(limit=10, offset=0)]
    assert names == ["Canada", "Mexico"]
    assert rm.get_team(1) is not None
    assert rm.get_team(999) is None


def test_bronze_loader_idempotency_on_postgres(tmp_path: Path) -> None:
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {_BRONZE} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {_BRONZE}"))
    (tmp_path / "teams.csv").write_text("team_id,team_name\n1,Mexico\n", encoding="utf-8")
    loader = BronzeLoader(engine, schema=_BRONZE)
    src = Source("teams.csv", "raw_teams")

    first = loader.load(src, tmp_path)
    second = loader.load(src, tmp_path)

    assert first.rows == 1 and not first.skipped
    assert second.skipped  # sha256 no-op on real Postgres, not just SQLite
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT count(*) FROM {_BRONZE}.raw_teams")).scalar_one()
    assert count == 1
