from __future__ import annotations

import weakref
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .ast import AST
from .infos import CommentInfo, ParseInfo
from .util import AsJSONMixin, asjson, asjsons

BASE_CLASS_TOKEN = '::'  # noqa: S105


@dataclass(eq=False)
class Node(AsJSONMixin):
    _parent: Node | None = None
    _children: list[Node] | None = None
    ast: AST | None = None
    ctx: Any = None
    parseinfo: ParseInfo | None = None

    def __init__(self, ast=None, **attributes):
        super().__init__()
        if isinstance(ast, dict):
            ast = AST(ast)
        self.ast = ast

        for name, value in attributes.items():
            setattr(self, name, value)

        self.__post_init__()

    def __post_init__(self):
        ast = self.ast

        if not self.parseinfo and isinstance(ast, AST):
            self.parseinfo = ast.parseinfo

        if not isinstance(ast, Mapping):
            return

        for name in set(ast) - {'parseinfo'}:
            try:
                setattr(self, name, ast[name])
            except AttributeError as e:
                raise AttributeError(f"'{name}' is a reserved name") from e

        self._children = self.children_list()
        if self.parseinfo is None:
            del self.parseinfo

    @property
    def parent(self):
        return self._parent

    @property
    def line(self):
        if self.parseinfo:
            return self.parseinfo.line
        return None

    @property
    def endline(self):
        if self.parseinfo:
            return self.parseinfo.endline
        return None

    def text_lines(self):
        if self.parseinfo:
            return self.parseinfo.text_lines()
        return None

    def line_index(self):
        return self.parseinfo.line_index()

    @property
    def col(self):
        return self.line_info.col if self.line_info else None

    @property
    def context(self):
        return self.ctx

    @property
    def line_info(self):
        if self.parseinfo:
            return self.parseinfo.tokenizer.line_info(self.parseinfo.pos)
        return None

    @property
    def text(self):
        if not self.parseinfo:
            return ''
        text = self.parseinfo.tokenizer.text
        return text[self.parseinfo.pos: self.parseinfo.endpos]

    @property
    def comments(self):
        if self.parseinfo:
            return self.parseinfo.tokenizer.comments(self.parseinfo.pos)
        return CommentInfo([], [])

    @property
    def _deref(self):
        # use this to get the actual object over weakref instances
        return self

    def _find_children(self):
        def with_parent(node):
            node._parent = weakref.proxy(self)
            return node

        def children_of(child):
            if isinstance(child, weakref.ReferenceType | weakref.ProxyType):
                return
            elif isinstance(child, Node):
                yield with_parent(child)
            elif isinstance(child, Mapping):
                for name, value in child.items():
                    if name.startswith('_'):
                        continue
                    yield from children_of(value)
            elif isinstance(child, list | tuple):
                yield from (
                    with_parent(c) for c in child if isinstance(c, Node)
                )

        children = list(self._pubdict().items())
        if not children:
            yield from children_of(self.ast)
        else:
            for name, child in children:
                if name.startswith('_'):
                    continue
                yield from children_of(child)

    def children_list(self):
        if self._children is not None:
            return self._children
        return list(self._find_children())

    def children_set(self):
        return set(self.children_list())

    def children(self):
        return self.children_list()

    def asjson(self):
        return asjson(self)

    def _pubdict(self):
        return {
            name: value
            for name, value in super()._pubdict().items()
            if name not in {'ast', 'ctx', 'parent', 'parseinfo'}
        }

    def __str__(self):
        return asjsons(self)

    def __hash__(self):
        if self.ast is not None:
            if isinstance(self.ast, list):
                return hash(tuple(self.ast))
            elif isinstance(self.ast, dict):
                return hash(AST(self.ast))
            else:
                return hash(self.ast)
        else:
            return id(self)

    def __eq__(self, other):
        if id(self) == id(other):
            return True
        elif self.ast is None:
            return False
        elif not getattr(other, 'ast', None):
            return False
        else:
            return self.ast == other.ast

    def _nonrefdict(self):
        return {
            name: value
            for name, value in vars(self).items()
            if (
                name not in {'_parent', '_children'}
                and type(value)
                not in {weakref.ReferenceType, weakref.ProxyType}
            )
        }

    # NOTE: pickling is important for parallel parsing
    def __getstate__(self):
        return self._nonrefdict()

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.children_list()


ParseModel = Node
