# notnone.py
from __future__ import annotations

from typing import Any, cast

__all__ = ['NotNone', 'Undefined']


class NotNoneType[T]:
    __notnone: Any = None

    def __init__(self):
        if isinstance(self.__notnone, NotNoneType):
            return
        type(self).__notnone = self

    @classmethod
    def notnone(cls) -> NotNoneType[T]:
        return cast(NotNoneType[T], cls.__notnone)

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


NotNone: NotNoneType[Any] = NotNoneType()
Undefined = NotNone
