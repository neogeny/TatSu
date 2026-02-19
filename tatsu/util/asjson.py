# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import enum
import inspect
import json
import weakref
from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from .abctools import as_namedtuple, isiter, rowselect

__all__ = [
    'AsJSONMixin',
    'JSONSerializable',
    'asjson',
    'asjsons',
    'plainjson',
]


@runtime_checkable
class JSONSerializable(Protocol):
    def __json__(self, seen: set[int] | None = None) -> Any: ...


class AsJSONMixin:
    __slots__ = ()

    def __json__(self, seen: set[int] | None = None) -> Any:
        pub = self.__pub__()
        return {
            '__class__': type(self).__name__,
            **asjson(pub, seen=seen),
        }

    def __pub__(self) -> dict[str, Any]:
        # Gemini (2026-01-26)
        def is_public(name: str, value: Any) -> bool:
            return not (name.startswith('_') or inspect.isroutine(value))

        return rowselect(dir(self), vars(self), where=is_public)


def asjson(obj: Any, seen: set[int] | None = None) -> Any:
    """
    Produce a JSON-serializable version of the input structure.
    """
    # Gemini (2026-01-26)
    seen = seen if seen is not None else set()

    def dfs(node: Any) -> Any:
        if node is None or isinstance(node, int | float | str | bool):
            return node

        node_id = id(node)
        if node_id in seen:
            return f"{type(node).__name__}@0x{hex(node_id).upper()[2:]}"

        seen.add(node_id)
        try:
            match node:
                case JSONSerializable() as serializable:
                    if not isinstance(serializable, type):
                        result = serializable.__json__(seen=seen)
                    else:
                        result = serializable
                case enum.Enum() as en:
                    result = dfs(en.value)
                case _ if isinstance(node, (weakref.ReferenceType, *weakref.ProxyTypes)):
                    result = f"{type(node).__name__}@0x{hex(node_id).upper()[2:]}"
                case _ if (nt := as_namedtuple(node)):
                    result = dfs(nt._asdict())
                case Mapping() as mapping:
                    result = {str(k): dfs(v) for k, v in mapping.items()}
                case list() | tuple() | set() as seq:
                    result = [dfs(e) for e in seq]
                case _ if isiter(node):
                    result = [dfs(e) for e in node]
                case _:
                    result = repr(node)
            return result
        finally:
            seen.discard(node_id)

    return dfs(obj)


def plainjson(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {
            name: plainjson(value)
            for name, value in obj.items()
            if name not in {'__class__', 'parseinfo'}
        }
    elif isinstance(obj, weakref.ReferenceType | weakref.ProxyType):
        return '@ref'
    elif isinstance(obj, str) and obj.startswith('@'):
        return '@ref'
    elif isiter(obj):
        return [plainjson(e) for e in obj]
    else:
        return obj


class FallbackJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that falls back to repr() for non-JSON-aware objects."""

    def default(self, o: Any) -> str:
        return repr(o)


def asjsons(obj: Any) -> str:
    return json.dumps(asjson(obj), indent=2, cls=FallbackJSONEncoder)
