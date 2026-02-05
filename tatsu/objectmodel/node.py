# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import functools
import weakref
from collections.abc import Iterable, Mapping
from typing import Any

from .base import BaseNode, TatSuDataclassParams

__all__ = ['Node']

from ..util.deprecate import deprecated


@dataclasses.dataclass(**TatSuDataclassParams)
class Node(BaseNode):
    __parent_ref: weakref.ref | None = None  # pyright: ignore[reportRedeclaration]

    def __init__(self, ast: Any = None, **kwargs: Any):
        super().__init__(ast=ast, **kwargs)
        self.__parent_ref: weakref.ref[Node] | None = None  # pyright: ignore[reportRedeclaration]

    def __post_init__(self):
        super().__post_init__()
        self.__parent_ref: weakref.ref[Node] | None = None

    @functools.cached_property
    def private_names(self) -> set[str]:
        return (
            {f.name for f in dataclasses.fields(Node)}
            | super().private_names
        )

    @property
    def parent(self) -> Node | None:  # pyright: ignore[reportGeneralTypeIssues]
        ref = self.__parent_ref
        if ref is None:
            return None
        else:
            return ref()

    @property
    def comments(self) -> Any:
        deprecated(replacement=None)(self.comments)
        return None

    @property
    def text(self) -> str | None:
        pi = self.parseinfo
        if pi and hasattr(pi.tokenizer, "text"):
            return pi.tokenizer.text[pi.pos : pi.endpos]
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
        return tuple(self._children())

    def children_list(self) -> list[Node]:
        return list(self._children())

    def _children(self) -> Iterable[Any]:
        def dfs(obj: Any) -> Iterable[Node]:
            match obj:
                case Node() as node:
                    node.__parent_ref = weakref.ref(self)
                    yield node
                case Mapping() as map:
                    for name, value in map.items():
                        if name.startswith("_"):
                            continue
                        if value is None:
                            continue
                        yield from dfs(value)
                case (list() | tuple()) as seq:
                    for item in seq:
                        yield from dfs(item)
                case _:
                    pass

        return tuple(dfs(self.__pubdict__()))
