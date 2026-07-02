"""Application ports consumed by the API layer, implemented by infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    """Outcome of a readiness probe (backend design §5, phased per M3 report)."""

    ready: bool
    failures: tuple[str, ...] = ()


class ReadinessProbe(Protocol):
    """Checks that the platform can actually serve (not merely run)."""

    def check(self) -> ReadinessReport: ...
