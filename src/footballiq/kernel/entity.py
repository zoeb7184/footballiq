"""Entity base class — identity-based equality.

Two entities are equal iff they are the same concrete type with the same
identity, regardless of attribute values. Value-based equality belongs to
value objects (`value_object.py`).
"""

from __future__ import annotations

from typing import Generic, TypeVar

IdT = TypeVar("IdT")


class Entity(Generic[IdT]):
    """Base for domain entities. Identity is immutable after construction."""

    __slots__ = ("_id",)

    def __init__(self, entity_id: IdT) -> None:
        self._id = entity_id

    @property
    def id(self) -> IdT:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        if type(self) is not type(other):
            return False
        return bool(self._id == other._id)

    def __hash__(self) -> int:
        return hash((type(self), self._id))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id!r})"
