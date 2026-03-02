# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses as dc
import functools
import weakref
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

from .basenode import BaseNode, tatsudataclass

__all__ = ['Node', 'tatsudataclass']


_children_cache: MutableMapping[Node, tuple[Node, ...]] = weakref.WeakKeyDictionary()


@tatsudataclass
class Node(BaseNode):
    _parent_ref: weakref.ref[Node] | None = dc.field(init=False, default=None)

    def __init__(self, ast: Any = None, **kwargs: Any):
        super().__init__(ast=ast, **kwargs)
        self._parent_ref = None

    @property
    def parent(self) -> Node | None:
        ref = self._parent_ref
        if ref is None:
            return None
        else:
            return ref()

    @property
    def comments(self) -> Any:
        return None

    @property
    def text(self) -> str | None:
        pi = self.parseinfo
        if pi and hasattr(pi.cursor, "text"):
            return pi.cursor.text[pi.pos : pi.endpos]
        return None

    @property
    def line(self) -> int | None:
        return self.parseinfo.line if self.parseinfo else None

    @property
    def path(self) -> tuple[Node, ...]:
        ancestors: list[Node] = [self]
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = parent.parent
        return tuple(reversed(ancestors))

    def children(self) -> tuple[Node, ...]:
        return self._cached_children()

    def children_list(self) -> list[Node]:
        return list(self._cached_children())

    def _cached_children(self) -> tuple[Node, ...]:
        def dfs(obj: Any) -> Iterable[Node]:
            match obj:
                case Node() as node:
                    node._parent_ref = weakref.ref(self)
                    yield node
                case Mapping() as mapping:
                    for name, value in mapping.items():
                        if name.startswith('_'):
                            continue
                        if value is None:
                            continue
                        yield from dfs(value)
                case bytes() | str():
                    pass
                case Iterable() as seq:
                    for item in seq:
                        yield from dfs(item)
                case _:
                    pass

        if self not in _children_cache:
            _children_cache[self] = tuple(dfs(self.__pub__()))
        return _children_cache[self]
