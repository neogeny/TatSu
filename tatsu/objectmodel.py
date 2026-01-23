from __future__ import annotations

import inspect
import warnings
import weakref
from collections.abc import Callable, Iterable, Mapping
from typing import Any, cast

from .ast import AST
from .infos import ParseInfo
from .tokenizing import CommentInfo
from .util import AsJSONMixin, asjson, asjsons

__all__ = ['BaseNode', 'Node']


class BaseNode(AsJSONMixin):
    # NOTE: declare at the class level in case __init__ is not called
    ast: Any = None
    parseinfo: ParseInfo | None = None
    __attributes: dict[str, Any] = {}  # noqa: RUF012

    def __init__(self, ast: Any = None, **kwargs: Any):
        super().__init__()
        self.ast: Any = ast
        self.parseinfo: ParseInfo | None = None
        self.__attributes: dict[str, Any] = {}

        if isinstance(ast, AST) and 'parseinfo' in ast:
            self.parseinfo = ast['parseinfo']

        # NOTE: the old objectmodel.Node would add new setattr(self, ...)
        allargs = ast | kwargs if isinstance(self.ast, AST) else kwargs
        self.__set_attributes(**allargs)

    def set_parseinfo(self, value: ParseInfo | None) -> None:
        self.parseinfo = value

    def __set_attributes(self, **attrs) -> None:
        for name, value in attrs.items():
            if hasattr(self, name) and not inspect.ismethod(getattr(self, name)):
                setattr(self, name, value)
            else:
                if hasattr(self, name):
                    warnings.warn(
                        f'"{name}" in keyword arguments will shadow'
                        f' {type(self).__name__}.{name}',
                        stacklevel=2,
                    )
                self.__attributes[name] = value

    def __getattr__(self, name: str) -> Any:
        # note: here only if normal attribute search failed
        try:
            assert isinstance(self.__attributes, dict)
            return self.__attributes[name]
        except KeyError:
            return super().__getattribute__(name)

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({', '.join(self._pubdict())})"
        )

    def __eq__(self, other) -> bool:
        # note: no use case for structural equality
        return id(self) == id(other)

    def __hash__(self) -> int:
        return hash(id(self))

    def __getstate__(self) -> Any:
        return self.__nonrefdict()

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __nonrefdict(self) -> Mapping[str, Any]:
        return {
            name: value if (
                    type(value) not in {weakref.ReferenceType, weakref.ProxyType}
            ) else None
            for name, value in vars(self).items()
        }


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

    def asjson(self) -> Any:
        return asjson(self)

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
