# isnotnone.py
from __future__ import annotations

from typing import Any, cast

__all__ = ['Undefined']


class UndefinedType[T]:
    __undefined: Any = None

    def __init__(self):
        if isinstance(self.__undefined, UndefinedType):
            return
        type(self).__undefined = self

    @classmethod
    def undefined(cls) -> UndefinedType[T]:
        return cast(UndefinedType[T], cls.__undefined)

    def __eq__(self, other: Any) -> bool:
        if self is not Undefined:
            return False
        if other is not Undefined:
            return False
        return other is self

    def __repr__(self) -> str:
        return 'Undefined'

    def __str__(self) -> str:
        return 'Undefined'

    def __hash__(self) -> int:
        return hash(id(self))


Undefined: UndefinedType[Any] = UndefinedType()
