"""Kernel error hierarchy.

Policy (Module 1 design decision):
- `InvariantViolation` is raised when domain rules are broken — these are
  bugs or bad data and must fail loudly.
- Expected operational failures (not found, contract breach at a boundary)
  are modelled with `Result` (see `result.py`), never exceptions.
"""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class InvariantViolation(DomainError):
    """A domain invariant was violated (bug or bad data — fail loudly)."""
