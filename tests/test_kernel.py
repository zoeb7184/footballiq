"""Kernel tests: Result semantics and Entity identity rules."""

import pytest

from footballiq.kernel.entity import Entity
from footballiq.kernel.result import Err, Ok


class _Order(Entity[int]):
    __slots__ = ()


class _Invoice(Entity[int]):
    __slots__ = ()


def test_ok_unwrap_and_map() -> None:
    assert Ok(2).unwrap() == 2
    assert Ok(2).map(lambda v: v * 10).unwrap() == 20
    assert Ok(2).unwrap_or(99) == 2


def test_err_unwrap_raises_and_map_is_noop() -> None:
    err: Err[str] = Err("boom")
    assert not err.is_ok()
    assert err.unwrap_or(99) == 99
    assert err.map(lambda v: v).error == "boom"
    with pytest.raises(RuntimeError, match="boom"):
        err.unwrap()


def test_entity_equality_is_identity_based() -> None:
    assert _Order(1) == _Order(1)
    assert _Order(1) != _Order(2)


def test_entities_of_different_types_never_equal() -> None:
    assert _Order(1) != _Invoice(1)


def test_entities_are_hashable_by_type_and_id() -> None:
    assert len({_Order(1), _Order(1), _Order(2), _Invoice(1)}) == 3
