"""Kernel ports — persistence abstractions implemented by infrastructure.

Application code depends on these protocols; concrete adapters (SQL, etc.)
live in the infrastructure layer and are bound at composition time.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, TypeVar

TEntity = TypeVar("TEntity")
IdT_contra = TypeVar("IdT_contra", contravariant=True)


class Repository(Protocol[TEntity, IdT_contra]):
    """Collection-like access to entities of one type."""

    def get(self, entity_id: IdT_contra) -> TEntity | None: ...

    def add(self, entity: TEntity) -> None: ...

    def list_all(self) -> list[TEntity]: ...


class UnitOfWork(Protocol):
    """Transactional boundary for a business operation."""

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
