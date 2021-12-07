from __future__ import annotations

from typing import Any
from functools import cache
from collections.abc import Mapping
from dataclasses import dataclass

from tatsu.util import asjson, asjsons
from tatsu.infos import CommentInfo, ParseInfo
from tatsu.ast import AST


BASE_CLASS_TOKEN = '::'


@dataclass(eq=False)
class Node:
    ast: AST|None = None
    ctx: Any = None
    parseinfo: ParseInfo|None = None

    def __init__(self, ast=None, **attributes):
        super().__init__()
        self._ast = self.ast = ast
        self._parent = None

        for name, value in attributes.items():
            setattr(self, name, value)

        self.__post_init__()
        # FIXME: why is this needed?
        del self.ast

    def __post_init__(self):
        ast = self._ast = self.ast

        if not self.parseinfo and isinstance(ast, AST):
            self.parseinfo = ast.parseinfo

        if not isinstance(ast, Mapping):
            return

        for name in set(ast) - {'parseinfo'}:
            try:
                setattr(self, name, ast[name])
            except AttributeError:
                raise AttributeError("'%s' is a reserved name" % name)

    def _get_ast(self):
        return self._ast

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

        for childname, child in self._pubdict().items():
            if childname in {'ast', 'parent'}:
                continue
            if isinstance(child, Node):
                yield with_parent(child)
            elif isinstance(child, Mapping):
                yield from (with_parent(c) for c in child.values() if isinstance(c, Node))
            elif isinstance(child, (list, tuple)):
                yield from (with_parent(c) for c in child if isinstance(c, Node))

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
            if not name.startswith('_') and name != 'ast'
        }

    def __json__(self):
        return asjson({
            '__class__': type(self).__name__,
            **self._pubdict()
        })

    def __str__(self):
        return asjsons(self)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if id(self) == id(other):
            return True
        elif not hasattr(self, '_ast'):
            return False
        elif not hasattr(other, '_ast'):
            return False
        else:
            return self._ast == other._ast

    # FIXME
    # def __getstate__(self):
    #     state = self._pubdict()
    #     return state
    #
    # def __setstate__(self, state):
    #     self.__dict__ = dict(state)


ParseModel = Node
