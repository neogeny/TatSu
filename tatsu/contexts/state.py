# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
from copy import copy
from typing import Any, Self

from ..ast import AST
from ..infos import Alert

__all__ = [
    'ParseState',
    'ParseStateStack',
]

from ..util.abctools import is_list


class ParseState:
    __slots__ = ('alerts', 'ast', 'cst', 'pos')

    def __init__(self, pos: int = 0, ast: Any = None, cst: Any = None):
        self.pos: int = pos
        self.ast: Any = ast or AST()
        self.cst: Any = cst
        self.alerts: list[Alert] = []

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
    def __init__(self: Self) -> None:
        self._state_stack: list[ParseState] = [ParseState()]
        self._last_node: Any = None
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
    def cst(self, value: Any) -> Any:
        self.top.cst = value
        return self.cst

    @property
    def pos(self) -> int:
        return self.top.pos

    @property
    def last_node(self) -> Any:
        return self._last_node

    @last_node.setter
    def last_node(self, value: Any) -> None:
        self._last_node = value

    def node(self) -> Any:
        return self.top.node()

    def pop(self) -> ParseState:
        return self._state_stack.pop()

    def _push(self, pos: int = 0, ast: Any = None, cst: Any = None) -> ParseState:
        self._state_stack.append(ParseState(pos=pos, ast=ast, cst=cst))
        return self.top

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

    def push_ast(self, pos: int, copyast: bool = False) -> Any:
        ast = copy(self.ast) if copyast else AST()
        self.state.pos = pos
        self._push(pos=pos, ast=ast)
        return self.ast

    def merge_ast(self) -> Any:
        prev = self.pop()
        self.ast = prev.ast
        self.extend_cst(prev.cst)
        return self.ast

    def push_cst(self) -> Any:
        self._push(ast=self.ast)
        return self.cst

    def pop_cst(self) -> Any:
        ast = self.ast
        cst = self.cst
        self.pop()
        self.ast = ast
        return cst

    def merge_cst(self) -> Any:
        cst = self.cst
        self.pop_cst()
        self.extend_cst(cst)
        return cst

    def append_cst(self, node: Any) -> Any:
        self.last_node = node
        previous = self.cst
        if previous is None:
            self.cst = self.copy_node(node)
        elif is_list(previous):
            previous.append(node)
        else:
            self.cst = [previous, node]
        return node

    def extend_cst(self, node: Any) -> Any:
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

    def name_last_node(self, name: str) -> None:
        self.ast[name] = self.last_node

    def add_last_node_to_name(self, name: str) -> None:
        self.ast._setlist(name, self.last_node)

    def define(self, keys: Iterable[str], list_keys: Iterable[str] | None = None) -> Any:
        ast = AST()
        ast._define(keys, list_keys=list_keys)
        ast.update(self.ast)
        self.ast = ast
        return self.ast

    def is_cut_set(self) -> bool:
        return self._cut_stack[-1]

    def push_cut(self):
        self._cut_stack.append(False)

    def pop_cut(self) -> bool:
        return self._cut_stack.pop()

    def set_cut_seen(self, prune: bool = True) -> None:
        self._cut_stack[-1] = True

    def ngpush(self, pos: int, ast: Any = None, cst: Any = None) -> ParseState:
        ast = copy(self.ast) if ast is None else ast
        self.state.pos = pos
        self._push(pos=pos, ast=ast, cst=cst)
        return self.top

    def ngmerge(self) -> ParseState:
        prev = self.pop()
        self.ast = prev.ast
        self.extend_cst(prev.cst)
        return prev

    def __old_pop_cst(self) -> Any:
        ast = self.ast
        cst = self.cst
        self.pop()
        self.ast = ast
        return cst

    def __expanded_merge_cst(self) -> Any:
        cst = self.cst

        ast = self.ast
        cst = self.cst
        self.pop()
        self.ast = ast
        self.extend_cst(cst)
