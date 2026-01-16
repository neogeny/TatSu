from __future__ import annotations

import copy
import operator
from collections.abc import Iterable
from functools import reduce
from typing import Any

from .infos import ParseInfo
from .util import asjson, is_list


class AST(dict[str, Any]):
    _frozen = False

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__()
        self.update(*args, **kwargs)
        self._frozen = True

    @property
    def frozen(self) -> bool:
        return self._frozen

    @property
    def parseinfo(self) -> ParseInfo | None:
        try:
            return super().__getitem__('parseinfo')
        except KeyError:
            return None

    def set_parseinfo(self, value: ParseInfo | None) -> None:
        if value is None:
            return
        super().__setitem__('parseinfo', value)

    def copy(self) -> AST:
        return copy.copy(self)

    def asjson(self) -> Any:
        return asjson(self)

    def _set(self, key: str, value: Any, force_list: bool = False) -> None:
        key = self._safekey(key)
        previous = self.get(key)

        if previous is None and force_list:
            value = [value]
        elif previous is None:
            pass
        elif is_list(previous):
            value = [*previous, value]
        else:
            value = [previous, value]

        super().__setitem__(key, value)

    def _setlist(self, key: str, value: list[Any]) -> None:
        self._set(key, value, force_list=True)

    def __copy__(self) -> AST:
        return AST(self)

    def __getitem__(self, key: str) -> Any:
        if key in self:
            return super().__getitem__(key)
        key = self._safekey(key)
        if key in self:
            return super().__getitem__(key)
        return None

    def __setitem__(self, key: str, value: Any) -> None:
        self._set(key, value)

    def __delitem__(self, key: str) -> None:
        key = self._safekey(key)
        super().__delitem__(key)

    def __setattr__(self, name: str, value: Any) -> None:
        if self._frozen and name not in vars(self):
            raise AttributeError(
                f'{type(self).__name__} attributes are fixed. '
                f' Cannot set attribute "{name}".',
            )
        super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:
        key = self._safekey(name)
        if key in self:
            return self[key]
        elif name in self:
            return self[name]

        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None

    def __hasattribute__(self, name: str) -> bool:
        try:
            super().__getattribute__(name)
        except (TypeError, AttributeError):
            return False
        else:
            return True

    def __reduce__(self) -> tuple[Any, Any]:
        return (AST, (list(self.items()),))

    def _safekey(self, key: str) -> str:
        while self.__hasattribute__(key):
            key += '_'
        return key

    def _define(self, keys: Iterable[str], list_keys: Iterable[str] | None = None):
        for key in (self._safekey(k) for k in keys):
            if key not in self:
                super().__setitem__(key, None)

        for key in (self._safekey(k) for k in list_keys or []):
            if key not in self:
                super().__setitem__(key, [])

    def __json__(self, seen: set[int] | None = None) -> Any:
        return {name: asjson(value, seen=seen) for name, value in self.items()}

    def __repr__(self) -> str:
        return f'AST{self.asjson()!r}'

    def __str__(self) -> str:
        return str(self.asjson())

    def __hash__(self) -> int:  # type: ignore
        return hash(
            reduce(
                operator.xor,
                (hash((name, id(value))) for name, value in self.items()),
                0,
            ),
        )
