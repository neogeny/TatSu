# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from copy import copy
from typing import Any

from ..ast import AST
from ..infos import Alert

__all__ = ['ParseState', 'ParseStateStack']

from ..tokenizing import Cursor, NullCursor

from ..util.abctools import is_list


class ParseState:
    __slots__ = ('_pos', 'alerts', 'ast', 'cst', 'cursor', 'last_node',)

    def __init__(self, cursor: Cursor, pos: int = 0, ast: Any = None, cst: Any = None):
        assert isinstance(cursor, Cursor), f'{type(cursor)} != NullCursor'
        self.cursor: Cursor = cursor.clonecursor()
        self._pos: int = pos
        self.ast: Any = ast or AST()
        self.cst: Any = cst
        self.last_node: Any = None
        self.alerts: list[Alert] = []

    @property
    def pos(self) -> int:
        assert not isinstance(self.cursor, NullCursor)
        # return self.cursor.pos
        return self._pos

    def goto(self, pos: int) -> None:
        assert not isinstance(self.cursor, NullCursor), f'{type(self.cursor)} != NullCursor'
        # self.cursor.goto(pos)
        self._pos = pos

    @property
    def node(self) -> Any:
        ast = self.ast
        cst = self.cst
        if not ast:
            return tuple(cst) if is_list(cst) else cst
        elif '@' in ast:
            return ast['@']
        else:
            return ast


class ParseStateStack:
    def __init__(self, cursor: Cursor) -> None:
        self._state_stack: list[ParseState] = [ParseState(cursor)]
        self._cut_stack: list[bool] = [False]

    @property
    def top(self) -> ParseState:
        return self._state_stack[-1]

    @property
    def state(self) -> ParseState:
        return self.top

    @property
    def ast(self) -> Any:
        return self.top.ast

    @ast.setter
    def ast(self, value: Any) -> None:
        self.top.ast = value

    @property
    def cst(self) -> Any:
        return self.top.cst

    @cst.setter
    def cst(self, value: Any):
        self.top.cst = value

    @property
    def cursor(self) -> Cursor:
        return self.top.cursor

    @property
    def pos(self) -> int:
        return self.top.pos

    @property
    def last_node(self) -> Any:
        return self.top.last_node

    @last_node.setter
    def last_node(self, value: Any) -> None:
        self.top.last_node = value

    @property
    def node(self) -> Any:
        return self.top.node

    def pop(self) -> ParseState:
        return self._state_stack.pop()

    def push(self, pos: int, ast: Any = None, cst: Any = None) -> ParseState:
        ast = copy(self.ast) if ast is None else ast
        self.state.goto(pos)

        newstate = ParseState(self.cursor, pos=pos, ast=ast, cst=cst)
        self._state_stack.append(newstate)

        return self.top

    def merge(self) -> ParseState:
        prev = self.pop()
        self.ast = prev.ast
        self.extend(prev.cst)
        return prev

    def alert(self, level: int = 1, message: str = '') -> Alert:
        self.top.alerts.append(Alert(level=level, message=message))
        return self.top.alerts[-1]

    @staticmethod
    def copy_node(node: Any) -> Any:
        if node is None:
            return None
        elif is_list(node):
            return node[:]
        else:
            return node

    def append(self, node: Any) -> Any:
        self.last_node = node
        previous = self.cst
        if previous is None:
            self.cst = self.copy_node(node)
        elif is_list(previous):
            previous.append(node)
        else:
            self.cst = [previous, node]
        return node

    def extend(self, node: Any) -> Any:
        self.last_node = node
        if node is None:
            return None
        previous = self.cst
        if previous is None:
            self.cst = self.copy_node(node)
        elif is_list(node):
            if is_list(previous):
                previous.extend(node)
            else:
                self.cst = [previous, *node]
        elif is_list(previous):
            previous.append(node)
        else:
            self.cst = [previous, node]
        return node

    def setname(self, name: str) -> None:
        self.ast._set(name, self.last_node)

    def addname(self, name: str) -> None:
        self.ast._setlist(name, self.last_node)

    def define(
        self,
        keys: Iterable[str],
        list_keys: Iterable[str] | None = None,
    ) -> Any:
        ast = AST()
        ast._define(keys, list_keys=list_keys)
        ast.update(self.ast)
        self.ast = ast
        return self.ast

    def cut_seen(self) -> bool:
        return self._cut_stack[-1]

    def push_cut(self):
        self._cut_stack.append(False)

    def pop_cut(self) -> bool:
        return self._cut_stack.pop()

    def set_cut_seen(self) -> None:
        self._cut_stack[-1] = True

    @contextmanager
    def cutscope(self):
        self.push_cut()
        try:
            yield
        finally:
            self.pop_cut()
