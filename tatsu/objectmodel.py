from __future__ import annotations

from typing import Any, Mapping
from functools import cache

from tatsu.util import asjson, asjsons
from tatsu.infos import CommentInfo, ParseInfo
from tatsu.ast import AST
# TODO: from tatsu.exceptions import NoParseInfo


BASE_CLASS_TOKEN = '::'


class _Node:
    pass


@cache
def wrapper(node: _Node) -> NodeWrapper:
    return NodeWrapper(node)


class Node(_Node):
    ctx: Any = None
    ast: AST|None = None
    parseinfo: ParseInfo|None = None

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        self.__postinit__()

    def __postinit__(self):
        if not self.parseinfo and isinstance(self.ast, AST):
            self.parseinfo = self.ast.parseinfo

        if not isinstance(self.ast, Mapping):
            return

        for name in set(self.ast) - {'parseinfo'}:
            try:
                setattr(self, name, self.ast[name])  # pylint: disable=E1136
            except AttributeError:
                pass

    def has_parseinfo(self):
        return self.parseinfo is not None

    def _pubdict(self):
        return {
            k: v
            for k, v in vars(self).items()
            if not k.startswith('_')
        }

    def __json__(self):
        return asjson({
            '__class__': type(self).__name__,
            **self._pubdict()
        })

    def __str__(self):
        return asjsons(self)

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    @property
    def line(self):
        return wrapper(self).line

    @property
    def endline(self):
        return wrapper(self).endline

    def text_lines(self):
        return wrapper(self).text_lines()

    def line_index(self):
        return wrapper(self).line_index()

    @property
    def col(self):
        return wrapper(self).col

    @property
    def line_info(self):
        return wrapper(self).line_info

    @property
    def text(self):
        return wrapper(self).text

    @property
    def comments(self):
        return wrapper(self).comments

    @property
    def children(self):
        return wrapper(self).children

    def children_list(self):
        return wrapper(self).children_list()

    def children_set(self):
        return wrapper(self).children_set()

    def asjson(self):
        return wrapper(self).asjson()


ParseModel = Node


class NodeWrapper:
    def __init__(self, node):
        self.node = node

    @property
    def line(self):
        if self.node.parseinfo:
            return self.node.parseinfo.line

    @property
    def endline(self):
        if self.node.parseinfo:
            return self.node.parseinfo.endline

    def text_lines(self):
        return self.node.parseinfo.text_lines()

    def line_index(self):
        return self.node.parseinfo.line_index()

    @property
    def col(self):
        return self.node.line_info.col if self.node.line_info else None

    @property
    def line_info(self):
        if self.node.parseinfo:
            return self.node.parseinfo.tokenizer.line_info(self.node.parseinfo.pos)

    @property
    def text(self):
        if not self.node.parseinfo:
            return ''
        text = self.node.parseinfo.tokenizer.text
        return text[self.node.parseinfo.pos:self.node.parseinfo.endpos]

    @property
    def comments(self):
        if self.node.parseinfo:
            return self.node.parseinfo.tokenizer.comments(self.node.parseinfo.pos)
        return CommentInfo([], [])

    @property
    def children(self):
        return self.node.children_list()

    def _children(self):
        for child in self.node._pubdict().values():
            if isinstance(child, Node):
                yield child
            elif isinstance(child, Mapping):
                yield from (c for c in child.values() if isinstance(c, Node))
            elif isinstance(child, (list, tuple)):
                yield from (c for c in child if isinstance(c, Node))

    @cache
    def children_list(self):
        return list(self._children())

    @cache
    def children_set(self):
        return set(self.children_list())

    def asjson(self):
        return asjson(self)
