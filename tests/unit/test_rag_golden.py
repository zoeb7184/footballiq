"""Golden-question eval (rag-design §9) — deterministic CI checks.

The 5 demo questions must route correctly, and the groundedness rule must hold:
every numeric token in a synthesized answer appears in the tool evidence. No
model, no DB — pure functions, so this runs in CI on every commit.
"""

from footballiq.application.rag.grounding import is_grounded
from footballiq.application.rag.ports import Fact, RetrievedChunk
from footballiq.application.rag.routing import classify

# The 5 demo questions -> their expected route (story 3, scope.md).
_GOLDEN_ROUTES = [
    ("What is the total squad value?", "kpi"),
    ("Which player is most undervalued?", "prediction"),
    ("What does the SHAP explanation represent?", "explanation"),
    ("Which club supplies the most talent value?", "graph"),
    ("What does the valuation model do?", "docs"),
]


def test_demo_questions_route_correctly() -> None:
    for question, expected in _GOLDEN_ROUTES:
        assert classify(question).value == expected, question


def test_answers_are_grounded_when_numbers_come_from_evidence() -> None:
    facts = [Fact("Total squad value (EUR)", "17143350000", "gold.dim_player")]
    chunks = [RetrievedChunk("c", "Squad value totals 17143350000 EUR.",
                             "docs/kpi.md", "KPI", 0.8)]
    assert is_grounded("The total squad value is 17143350000 EUR.", facts, chunks)


def test_fabricated_number_is_flagged_ungrounded() -> None:
    facts = [Fact("Total squad value (EUR)", "17143350000", "gold.dim_player")]
    # 42 appears in neither the fact nor any chunk -> must be caught
    assert not is_grounded("The value is 42 billion.", facts, [])
