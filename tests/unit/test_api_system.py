"""System endpoint tests — ring 1 (fake ports, no DB) per backend design §7."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from footballiq.api.main import create_app
from footballiq.application.ports import ReadinessProbe, ReadinessReport
from footballiq.infrastructure.config import Settings
from footballiq.infrastructure.gold.readiness import GoldReadinessProbe


class _FakeProbe(ReadinessProbe):
    def __init__(self, report: ReadinessReport) -> None:
        self._report = report

    def check(self) -> ReadinessReport:
        return self._report


def _client(report: ReadinessReport | None = None) -> TestClient:
    app = create_app(Settings(database_url="sqlite://", data_dir=Path("data/raw")))
    if report is not None:
        app.state.probe = _FakeProbe(report)
    return TestClient(app, raise_server_exceptions=False)


def test_health_is_always_alive() -> None:
    resp = _client().get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_ready_when_probe_passes() -> None:
    resp = _client(ReadinessReport(ready=True)).get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_not_ready_returns_503_with_reasons() -> None:
    report = ReadinessReport(ready=False, failures=("gold.fact_match is empty",))
    resp = _client(report).get("/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "not_ready"
    assert "empty" in body["failures"][0]


def test_unknown_route_is_problem_json() -> None:
    resp = _client().get("/nope")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["status"] == 404
    assert "correlation_id" in resp.json()


def test_gold_probe_reports_unreachable_warehouse() -> None:
    probe = GoldReadinessProbe(
        create_engine("postgresql+psycopg://nobody:nothing@127.0.0.1:1/void"),
        schema="gold",
    )
    report = probe.check()
    assert not report.ready
    assert "unreachable" in report.failures[0]


def test_gold_probe_requires_populated_fact_match() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE fact_match (match_id INTEGER)"))
    probe = GoldReadinessProbe(engine, schema=None)
    assert not probe.check().ready  # table exists but empty

    with engine.begin() as conn:
        conn.execute(text("INSERT INTO fact_match VALUES (1)"))
    assert probe.check().ready
