"""Result type for expected operational failures (Ok | Err).

Used at application boundaries where failure is a normal outcome.
Domain invariant violations raise `InvariantViolation` instead — see
`errors.py` for the split policy.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Successful outcome carrying a value."""

    value: T

    def is_ok(self) -> bool:
        return True

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:  # noqa: ARG002 - symmetry with Err
        return self.value

    def map(self, fn: Callable[[T], U]) -> Ok[U]:
        return Ok(fn(self.value))


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Failed outcome carrying an error description."""

    error: E

    def is_ok(self) -> bool:
        return False

    def unwrap(self) -> object:
        msg = f"called unwrap on Err: {self.error!r}"
        raise RuntimeError(msg)

    def unwrap_or(self, default: T) -> T:
        return default

    def map(self, fn: Callable[[object], object]) -> Err[E]:  # noqa: ARG002
        return self


Result = Ok[T] | Err[E]
