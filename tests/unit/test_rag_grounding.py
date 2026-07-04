"""Numeric groundedness tests (rag-design §9) — the load-bearing guarantee."""

from footballiq.application.rag.grounding import is_grounded, numeric_tokens
from footballiq.application.rag.ports import Fact, RetrievedChunk


def test_numeric_tokens_strip_separators() -> None:
    assert numeric_tokens("value is 17,140,000,000 and 49.8%") == {
        "17140000000", "49.8"}
    assert numeric_tokens("no digits here") == set()


def _fact(value: str) -> Fact:
    return Fact("label", value, "gold.x")


def _chunk(content: str) -> RetrievedChunk:
    return RetrievedChunk("id", content, "docs/x.md", "S", 0.9)


def test_grounded_when_numbers_come_from_facts() -> None:
    assert is_grounded("Total value: 17140000000", [_fact("17140000000")], [])


def test_grounded_when_number_is_in_a_retrieved_chunk() -> None:
    assert is_grounded("It was 223 goals", [], [_chunk("There were 223 goals.")])


def test_not_grounded_when_number_absent_from_evidence() -> None:
    # 999 appears nowhere in facts or chunks -> ungrounded
    assert not is_grounded("The answer is 999", [_fact("42")], [_chunk("about 42")])
