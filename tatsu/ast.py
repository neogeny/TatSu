# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, override

from .infos import ParseInfo
from .util import asjson
from .util.itertools import is_list
from .util.safeeval import make_hashable


class AST(dict[str, Any]):
    """
    A dictionary that allows attribute-style access to its keys.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__()
        self.__dict__['_frozen'] = False
        self.update(*args, **kwargs)
        self.__dict__['_frozen'] = True

    @property
    def parseinfo(self) -> ParseInfo | None:
        return self.get('parseinfo')

    # NOTE: required to bypass '_frozen'
    def set_parseinfo(self, value: ParseInfo | None) -> None:
        super().__setitem__('parseinfo', value)

    def asjson(self) -> Any:
        return asjson(self)

    def _set(self, key: str, value: Any, force_list: bool = False) -> None:
        key = self._safekey(key)
        previous = self.get(key)
        if previous is None:
            super().__setitem__(key, [value] if force_list else value)
        elif is_list(previous):
            super().__setitem__(key, [*previous, value])
        else:
            super().__setitem__(key, [previous, value])

    def _setlist(self, key: str, value: list[Any]) -> None:
        self._set(key, value, force_list=True)

    def _safekey(self, key: str) -> str:
        while key in dir(self):
            key += '_'
        return key

    def _define(self, keys: Iterable[str], list_keys: Iterable[str] | None = None):
        for key in (self._safekey(k) for k in keys):
            if key not in self:
                super().__setitem__(key, None)
        for key in (self._safekey(k) for k in list_keys or []):
            if key not in self:
                super().__setitem__(key, [])

    def __copy__(self) -> AST:
        return type(self)(self)

    def __getitem__(self, key: str) -> Any:
        if key in self:
            return super().__getitem__(key)
        return super().get(self._safekey(key))

    def __setitem__(self, key: Any, value: Any) -> None:
        self._set(key, value)

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(self._safekey(key))

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            self.__dict__[name] = value
            return
        if self.__dict__.get('_frozen'):
            raise AttributeError(f'AST attributes are fixed. Cannot set "{name}".')
        self[name] = value

    def __getattr__(self, name: str) -> Any:
        return self[name]

    def __reduce__(self) -> tuple[Any, Any]:
        return AST, (tuple(self.items()),)

    def __repr__(self) -> str:
        return f'AST({super().__repr__()})'

    def __str__(self) -> str:
        return str(self.asjson())

    @override
    def __hash__(self) -> int:  # pyright: ignore[reportIncompatibleVariableOverride]
        return hash(make_hashable(self))
