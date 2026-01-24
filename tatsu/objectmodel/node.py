from __future__ import annotations

import weakref
from collections.abc import Callable, Iterable, Mapping
from typing import Any, cast

from ..tokenizing import CommentInfo
from .base import BaseNode

__all__ = ['Node']


class Node(BaseNode):
    # NOTE: declare at the class level in case __init__ is not called
    ctx: Any = None
    __parent_ref: weakref.ref | None = None

    def __init__(self, ast: Any = None, ctx: Any = None, **kwargs: Any):
        super().__init__(ast=ast, **kwargs)
        self.ctx: Any = ctx
        self.__parent_ref: weakref.ref[Node] | None = None

    @property
    def parent(self) -> Node | None:
        ref = self.__parent_ref
        if ref is None:
            return None
        else:
            return ref()

    @property
    def comments(self) -> CommentInfo:
        if self.parseinfo and hasattr(self.parseinfo.tokenizer, 'comments'):
            comments = cast(Callable, self.parseinfo.tokenizer.comments)
            return comments(self.parseinfo.pos)
        return CommentInfo([], [])

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

    def children_list(self) -> list[Node]:
        return list(self.children())

    def children(self) -> Iterable[Any]:
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

        return tuple(dfs(self._pubdict()))
