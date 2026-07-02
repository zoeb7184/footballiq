"""ValueObject marker.

Value objects are immutable and equal by value. Implement them as
`@dataclass(frozen=True, slots=True)` classes inheriting this marker;
validate invariants in `__post_init__` and raise `InvariantViolation`.
The marker exists so architectural tooling and readers can identify value
objects structurally.
"""


class ValueObject:
    """Marker base class for value objects (frozen dataclasses)."""

    __slots__ = ()
