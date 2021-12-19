from __future__ import annotations

from typing import Any
from functools import cache
from collections.abc import Mapping
from dataclasses import dataclass

from .util import asjson, asjsons
from .infos import CommentInfo, ParseInfo
from .ast import AST


BASE_CLASS_TOKEN = '::'


@dataclass(eq=False)
class Node:
    _parent: Node|None = None
    ast: AST|None = None
    ctx: Any = None
    parseinfo: ParseInfo|None = None

    def __init__(self, ast=None, **attributes):
        super().__init__()
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
            except AttributeError:
                raise AttributeError("'%s' is a reserved name" % name)

    @property
    def parent(self):
        return self._parent

    @property
    def line(self):
        if self.parseinfo:
            return self.parseinfo.line

    @property
    def endline(self):
        if self.parseinfo:
            return self.parseinfo.endline

    def text_lines(self):
        if self.parseinfo:
            return self.parseinfo.text_lines()

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

    @property
    def text(self):
        if not self.parseinfo:
            return ''
        text = self.parseinfo.tokenizer.text
        return text[self.parseinfo.pos:self.parseinfo.endpos]

    @property
    def comments(self):
        if self.parseinfo:
            return self.parseinfo.tokenizer.comments(self.parseinfo.pos)
        return CommentInfo([], [])

    def _children(self):
        def with_parent(node):
            node._parent = self
            return node

        def children_of(child):
            if isinstance(child, Node):
                yield with_parent(child)
            elif isinstance(child, Mapping):
                yield from (with_parent(c) for c in child.values() if isinstance(c, Node))
            elif isinstance(child, (list, tuple)):
                yield from (with_parent(c) for c in child if isinstance(c, Node))

        children = list(self._pubdict().items())
        if not children:
            yield from children_of(self.ast)
        else:
            for _, child in children:
                yield from children_of(child)

    @cache
    def children_list(self):
        return list(self._children())

    @cache
    def children_set(self):
        return set(self.children_list())

    def children(self):
        return self.children_list()

    def asjson(self):
        return asjson(self)

    def _pubdict(self):
        return {
            name: value
            for name, value in vars(self).items()
            if not name.startswith('_') and name not in {'ast', 'ctx', 'parent'}
        }

    def __json__(self):
        return asjson({
            '__class__': type(self).__name__,
            **self._pubdict()
        })

    def __str__(self):
        return asjsons(self)

    def __hash__(self):
        if self.ast is not None:
            if isinstance(self.ast, list):
                return hash(tuple(self.ast))
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

    # FIXME
    # def __getstate__(self):
    #     state = self._pubdict()
    #     return state
    #
    # def __setstate__(self, state):
    #     self.__dict__ = dict(state)


ParseModel = Node
