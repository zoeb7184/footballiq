"""Match adapter against a miniature star schema (SQLite, schema=None)."""

from sqlalchemy import Engine, create_engine, text

from footballiq.infrastructure.gold.matches import GoldMatchReadModel


def _star() -> Engine:
    engine = create_engine("sqlite://")
    ddl = [
        "CREATE TABLE dim_stage (stage_sk int, stage_name text, is_knockout int)",
        "CREATE TABLE dim_venue (venue_sk int, stadium_name text)",
        "CREATE TABLE dim_team (team_sk int, team_id_nat int, team_name text, fifa_code text)",
        "CREATE TABLE dim_date (date_key int, calendar_date text)",
        (
            "CREATE TABLE fact_match (match_id int, date_key int, kickoff_utc text, "
            "stage_sk int, venue_sk int, home_team_sk int, away_team_sk int, "
            "status text, home_score int, away_score int, home_xg real, away_xg real)"
        ),
    ]
    rows = [
        "INSERT INTO dim_stage VALUES (1,'Group Stage',0), (3,'Round of 16',1)",
        "INSERT INTO dim_venue VALUES (1,'Estadio Azteca'), (2,'MetLife')",
        (
            "INSERT INTO dim_team VALUES (1,1,'Mexico','MEX'), (2,2,'South Africa','RSA'), "
            "(-1,NULL,'Unknown','UNK'), (-2,NULL,'To Be Determined','TBD')"
        ),
        "INSERT INTO dim_date VALUES (20260611,'2026-06-11'), (20260704,'2026-07-04')",
        (
            "INSERT INTO fact_match VALUES "
            "(1,20260611,'19:00',1,1,1,2,'Completed',2,0,1.84,0.52), "
            "(89,20260704,'21:00',3,2,1,-2,'Scheduled',NULL,NULL,NULL,NULL)"
        ),
    ]
    with engine.begin() as conn:
        for stmt in ddl + rows:
            conn.execute(text(stmt))
    return engine


def test_completed_match_record_fully_typed() -> None:
    rm = GoldMatchReadModel(_star(), schema=None)
    rec = rm.get_match(1)
    assert rec is not None
    assert rec.status == "Completed"
    assert rec.away_team is not None and rec.away_team.fifa_code == "RSA"
    assert rec.home_score == 2 and rec.home_xg == 1.84
    assert rec.match_date == "2026-06-11"
    assert rec.is_knockout is False


def test_reserved_away_member_becomes_none_for_dto_layer() -> None:
    rm = GoldMatchReadModel(_star(), schema=None)
    rec = rm.get_match(89)
    assert rec is not None
    assert rec.away_team is None  # -2 (TBD) never leaks as a fake team
    assert rec.is_knockout is True


def test_list_ordering_filter_and_count() -> None:
    rm = GoldMatchReadModel(_star(), schema=None)
    assert [m.match_id for m in rm.list_matches(limit=10, offset=0, status=None)] == [1, 89]
    assert rm.count_matches(status="Scheduled") == 1
    only_done = rm.list_matches(limit=10, offset=0, status="Completed")
    assert [m.match_id for m in only_done] == [1]
