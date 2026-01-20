from __future__ import annotations

import inspect
import weakref
from collections.abc import Callable, Iterable, Mapping
from typing import Any, cast

from .ast import AST
from .infos import ParseInfo
from .tokenizing import CommentInfo
from .util import AsJSONMixin, asjson, asjsons

__all__ = ['Node']


class Node(AsJSONMixin):
    # NOTE: declare at the class level in case __init__ is not called
    ast: Any = None
    ctx: Any = None
    parseinfo: ParseInfo | None = None

    _attributes: dict[str, Any] = {}  # noqa: RUF012
    _parent_ref: weakref.ref | None = None

    def __init__(self, ast: Any = None, ctx: Any = None, **kwargs: Any):
        super().__init__()
        self.ast: Any = ast
        self.ctx: Any = ctx
        self.parseinfo: ParseInfo | None = None
        self._attributes: dict[str, Any] = {}
        self._parent_ref: weakref.ref[Node] | None = None

        # NOTE: objectmodel.Node would create new attributes
        allargs = ast | kwargs if isinstance(self.ast, AST) else kwargs
        for name, value in allargs.items():
            if hasattr(self, name) and not inspect.ismethod(getattr(self, name)):
                setattr(self, name, value)
            else:
                # may shadow a predefined heree
                self._attributes[name] = value

    def __getattr__(self, name: str) -> Any:
        # note: here only if normal attribute search failed
        try:
            assert isinstance(self._attributes, dict)
            return self._attributes[name]
        except KeyError:
            return super().__getattribute__(name)
            # # NOTE: signals hasattr() and the likes that the name was not found
            # raise AttributeError(
            #     f'"{name}" is not a valid attribute in {type(self).__name__}',
            # ) from e

    def set_parseinfo(self, value: ParseInfo | None) -> None:
        self.parseinfo = value

    @property
    def parent(self) -> Node | None:
        ref = self._parent_ref
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
        ancestors: list[Node] = []
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = parent.parent
        return tuple(reversed(ancestors))

    def children_list(self) -> list[Node]:
        return list(self.children())

    def children(self) -> Iterable[Any]:
        def walk(obj: Any) -> Iterable[Node]:
            match obj:
                case Node() as node:
                    self._parent_ref = weakref.ref(self)
                    yield node
                case Mapping() as map:
                    for name, value in map.items():
                        if name.startswith("_"):
                            continue
                        if value is None:
                            continue
                        yield from walk(value)
                case (list() | tuple()) as seq:
                    for item in seq:
                        yield from walk(item)
                case _:
                    pass

        return tuple(walk(self._pubdict()))

    def __str__(self) -> str:
        return asjsons(self)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({', '.join(self._pubdict())})"
        )

    def __eq__(self, other) -> bool:
        if id(self) == id(other):
            return True
        elif self.ast is None:
            return False
        elif not getattr(other, 'ast', None):
            return False
        else:
            return self.ast == other.ast

    def __hash__(self) -> int:
        if self.ast is None:
            return id(self)
        elif isinstance(self.ast, list):
            return hash(tuple(self.ast))
        elif isinstance(self.ast, dict):
            return hash(AST(self.ast))
        else:
            return hash(self.ast)

    def __getstate__(self) -> Any:
        return self._nonrefdict()

    def __setstate__(self, state):
        self.__dict__.update(state)

    def _nonrefdict(self) -> Mapping[str, Any]:
        return {
            name: value
            for name, value in vars(self).items()
            if (
                    name not in {'_parent', '_children'}
                    and type(value)
                    not in {weakref.ReferenceType, weakref.ProxyType}
            )
        }
