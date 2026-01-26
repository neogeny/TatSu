from __future__ import annotations

from typing import Any, cast

__all__ = ['Undefined']


class UndefinedType[T]:
    _undefined: UndefinedType[T] | None = None

    def __init__(self) -> None:
        type(self)._undefined = UndefinedType[T]()

    @classmethod
    def undefined(cls) -> UndefinedType[T]:
        return cast(UndefinedType[T], cls._undefined)

    def __hash__(self) -> int:
        return hash(id(self))


Undefined: UndefinedType[Any] = UndefinedType.undefined()
