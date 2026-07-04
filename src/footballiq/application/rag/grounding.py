"""Numeric groundedness (rag-design §9).

The load-bearing guarantee: every number that appears in an answer must also
appear in the tool evidence (SQL facts or retrieved chunks). If a numeric token
in the answer isn't in the evidence, the answer is not grounded — the pipeline
must not present it as fact. Deterministic and CI-checkable.
"""

from __future__ import annotations

import re

from footballiq.application.rag.ports import Fact, RetrievedChunk

# A numeric token: digits with optional thousands separators / decimals / %.
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numeric_tokens(text: str) -> set[str]:
    """Normalized numeric tokens in text (thousands separators stripped)."""
    return {m.replace(",", "") for m in _NUMBER.findall(text)}


def is_grounded(
    answer: str, facts: list[Fact], chunks: list[RetrievedChunk]
) -> bool:
    """True iff every number in the answer appears in the evidence."""
    evidence = " ".join([f.value for f in facts] + [c.content for c in chunks])
    return numeric_tokens(answer) <= numeric_tokens(evidence)
