# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any, cast

__all__ = ['NotNone', 'NotNoneType', 'Undefined', 'UndefinedType']


def notnone[T](value: T | None, default: T) -> T:
    return value if value is not None else default


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

    def __bool__(self):
        return False

    def __and__(self, other):
        return self

    def __rand__(self, other):
        return self.__and__(other)

    def __or__(self, other):
        return other

    def __ror__(self, other):
        return self.__or__(other)

    def __invert__(self):
        return not None

    def __repr__(self) -> str:
        return 'Undefined'

    def __str__(self) -> str:
        return 'Undefined'

    def __hash__(self) -> int:
        return hash(id(self))


UndefinedType = NotNoneType
NotNone: NotNoneType[Any] = NotNoneType()
Undefined = NotNone
