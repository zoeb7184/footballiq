"""Route classification tests (rag-design §1) — deterministic keyword routing."""

from footballiq.application.rag.ports import Route
from footballiq.application.rag.routing import classify


def test_routes_by_keyword() -> None:
    assert classify("Why is this player valued so high?") == Route.EXPLANATION
    assert classify("Which players are most undervalued?") == Route.PREDICTION
    assert classify("Which clubs are the biggest talent suppliers?") == Route.GRAPH
    assert classify("How many goals were scored?") == Route.KPI


def test_explanation_wins_over_prediction() -> None:
    # "why ... undervalued" -> explanation takes precedence (ordered rules)
    assert classify("Why is he undervalued?") == Route.EXPLANATION


def test_unmatched_falls_back_to_docs() -> None:
    assert classify("What is clean architecture?") == Route.DOCS
