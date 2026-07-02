"""Bronze loader tests — SQLite in-memory (loader is engine-agnostic)."""

from pathlib import Path

from sqlalchemy import create_engine, text

from footballiq.infrastructure.ingestion.bronze import BronzeLoader
from footballiq.infrastructure.ingestion.manifest import SOURCES, Source


def _write_csv(tmp_path: Path, name: str, content: str) -> None:
    (tmp_path / name).write_text(content, encoding="utf-8")


def test_manifest_covers_all_eleven_sources() -> None:
    assert len(SOURCES) == 11
    assert {s.filename for s in SOURCES} == {
        "teams.csv", "venues.csv", "tournament_stages.csv", "referees.csv",
        "matches.csv", "matches_detailed.csv", "squads_and_players.csv",
        "player_stats.csv", "match_team_stats.csv", "match_lineups.csv",
        "match_events.csv",
    }
    bronze_only = {s.filename for s in SOURCES if s.bronze_only}
    assert bronze_only == {"matches_detailed.csv"}  # reconciliation fixture


def test_load_stamps_metadata_and_registers(tmp_path: Path) -> None:
    _write_csv(tmp_path, "teams.csv", "team_id,team_name\n1,Mexico\n2,South Africa\n")
    engine = create_engine("sqlite://")
    loader = BronzeLoader(engine, schema=None)

    result = loader.load(Source("teams.csv", "raw_teams"), tmp_path)

    assert not result.skipped
    assert result.rows == 2
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM raw_teams")).mappings().all()
        assert len(rows) == 2
        assert rows[0]["team_name"] == "Mexico"
        assert rows[0]["_load_id"] == result.load_id  # stamped
        registry = conn.execute(text("SELECT * FROM _loads")).mappings().one()
        assert registry["row_count"] == 2


def test_unchanged_file_is_recorded_noop(tmp_path: Path) -> None:
    _write_csv(tmp_path, "teams.csv", "team_id,team_name\n1,Mexico\n")
    engine = create_engine("sqlite://")
    loader = BronzeLoader(engine, schema=None)
    src = Source("teams.csv", "raw_teams")

    first = loader.load(src, tmp_path)
    second = loader.load(src, tmp_path)

    assert not first.skipped
    assert second.skipped  # idempotency: same bytes -> no-op
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw_teams")).scalar_one()
        assert count == 1  # no duplicate rows


def test_changed_file_appends_new_load(tmp_path: Path) -> None:
    engine = create_engine("sqlite://")
    loader = BronzeLoader(engine, schema=None)
    src = Source("teams.csv", "raw_teams")

    _write_csv(tmp_path, "teams.csv", "team_id,team_name\n1,Mexico\n")
    loader.load(src, tmp_path)
    _write_csv(tmp_path, "teams.csv", "team_id,team_name\n1,Mexico\n2,Canada\n")
    result = loader.load(src, tmp_path)

    assert not result.skipped
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw_teams")).scalar_one()
        loads = conn.execute(text("SELECT COUNT(*) FROM _loads")).scalar_one()
    assert count == 3  # append-only: 1 + 2 (silver dedupes by latest load)
    assert loads == 2
