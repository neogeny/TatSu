# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from copy import copy
from typing import Any, Self, overload

from .ast import AST
from .cst import cstadd, cstfinal, cstmerge
from .infos import Alert, RuleInfo

__all__ = ['ParseState', 'ParseStateStack']

from ..tokenizing import Cursor
from ..util import typename


class ParseState:
    __slots__ = (
        'alerts',
        'ast',
        'cst',
        'cursor',
        'last_node',
    )

    def __init__(self, base: Cursor | ParseState) -> None:
        if isinstance(base, ParseState):
            self.cursor: Cursor = base.cursor.clone()
            self.ast: AST = copy(base.ast)
        else:
            self.cursor = base.clone()
            self.ast = AST()

        self.cst: Any = None
        self.last_node: Any = None
        self.alerts: list[Alert] = []

    def clone(self):
        return copy(self)

    def goto(self, pos: int) -> None:
        self.cursor.goto(pos)

    def merge(self, prev: ParseState) -> Self:
        self.ast = prev.ast
        self.extend(prev.cst)
        self.alerts.extend(prev.alerts)
        self.goto(prev.pos)
        return self

    @property
    def pos(self) -> int:
        return self.cursor.pos

    @property
    def node(self) -> Any:
        ast = self.ast
        cst = self.cst
        if not ast:
            return cstfinal(cst)
        elif '@' in ast:
            return ast['@']
        else:
            return ast

    def __copy__(self) -> ParseState:
        new = ParseState(self.cursor)
        new.alerts = self.alerts[:]
        return new

    def append(self, node: Any, aslist: bool = False) -> Any:
        self.last_node = node
        self.cst = cstadd(self.cst, node, aslist=aslist)
        return node

    def extend(self, node: Any) -> Any:
        self.last_node = node
        self.cst = cstmerge(self.cst, node)
        return node

    def nameset(self, name: str) -> None:
        self.ast._set(name, self.last_node)

    def nameadd(self, name: str) -> None:
        self.ast._set(name, self.last_node, aslist=True)

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

    @overload
    def __call__(self, node: ParseState) -> Self: ...

    @overload
    def __call__(self, node: Any) -> Any: ...

    @overload
    def __call__(self, **kwargs: Any) -> Any: ...

    def __call__(self, node: Any = None, **kwargs: Any) -> Any:
        if node is not None and kwargs:
            raise TypeError("Cannot provide both a positional and keyword arguments.")
        if node is None and not kwargs:
            raise TypeError(
                "Must provide either one positional argument or keyword arguments."
            )

        if isinstance(node, ParseState):
            return self.merge(node)
        elif kwargs:
            for name, value in kwargs.items():
                self.append(value)
                self.nameset(name)
            return self.last_node
        elif node is None:
            return None
        else:
            return self.append(node)


class ParseStateStack:
    __slots__ = ('_cut_stack', '_ruleinfo_stack', '_state_stack', 'lookahead')

    def __init__(self, cursor: Cursor) -> None:
        self.lookahead: int = 0
        self._state_stack: list[ParseState] = [ParseState(cursor)]
        self._cut_stack: list[bool] = [False]
        self._ruleinfo_stack: list[RuleInfo] = []

    def clone(self):
        return copy(self)

    @property
    def top(self) -> ParseState:
        return self._state_stack[-1]

    @property
    def state(self) -> ParseState:
        return self._state_stack[-1]

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

    def pop(self, pos: int | None = None) -> ParseState:
        prev = self._state_stack.pop()
        if pos is not None:
            self.state.goto(pos)
        return prev

    def new(self) -> ParseState:
        newstate = ParseState(self.cursor)
        self._state_stack.append(newstate)
        return self.top

    def push(self) -> ParseState:
        newstate = ParseState(self.state)
        self._state_stack.append(newstate)

        return self.top

    def merge(self) -> ParseState:
        prev = self.pop()
        return self.state.merge(prev)

    def alert(self, level: int = 1, message: str = '') -> Alert:
        self.top.alerts.append(Alert(level=level, message=message))
        return self.top.alerts[-1]

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

    @property
    def ruleinfo_stack(self) -> list[RuleInfo]:
        return self._ruleinfo_stack

    def __copy__(self) -> ParseStateStack:
        new = self.__class__.__new__(self.__class__)

        new._state_stack = self._state_stack[:]
        new._cut_stack = self._cut_stack[:]
        new._ruleinfo_stack = self._ruleinfo_stack[:]

        return new
