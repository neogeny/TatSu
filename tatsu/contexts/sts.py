# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
from copy import copy
from typing import Any, Self, overload

from .ast import AST
from .cst import cstadd, cstfinal, cstmerge
from .infos import Alert, RuleInfo


__all__ = ['ParseState', 'ParseStateStack']

from ..input import Cursor


_AT_ = '__vallue__'


class ParseState:
    __slots__ = (
        'alerts',
        'ast',
        'cst',
        'cursor',
        'cutseen',
        'last_node',
    )

    def __init__(self, base: Cursor | ParseState) -> None:
        if isinstance(base, ParseState):
            self.cursor: Cursor = copy(base.cursor)
            self.ast: AST = copy(base.ast)
        else:
            self.cursor = copy(base)
            self.ast = AST()

        self.cst: Any = None
        self.cutseen: bool = False
        self.last_node: Any = None
        self.alerts: list[Alert] = []

    def clone(self) -> Self:
        return copy(self)

    def __copy__(self) -> Self:
        new = type(self)(self.cursor)
        new.alerts = self.alerts[:]
        return new

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
    def parsed(self) -> Any:
        ast = self.ast
        cst = self.cst
        if not ast:
            return cstfinal(cst)
        elif _AT_ in ast:
            return ast[_AT_]
        else:
            return ast

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

    def __call__(self, *args, node: Any = None, **kwargs: Any) -> Any:
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
    __slots__ = ('ruleinfo_stack', 'state_stack')

    def __init__(self, cursor: Cursor) -> None:
        self.state_stack: list[ParseState] = [ParseState(cursor)]
        self.ruleinfo_stack: list[RuleInfo] = []

    def clone(self) -> Self:
        return copy(self)

    @property
    def top(self) -> ParseState:
        return self.state_stack[-1]

    @property
    def state(self) -> ParseState:
        return self.state_stack[-1]

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
    def parsed(self) -> Any:
        return self.top.parsed

    def pop(self, pos: int | None = None) -> ParseState:
        prev = self.state_stack.pop()
        if pos is not None:
            self.state.goto(pos)
        return prev

    def new(self) -> ParseState:
        newstate = ParseState(self.cursor)
        self.state_stack.append(newstate)
        return self.top

    def push(self) -> ParseState:
        newstate = ParseState(self.state)
        self.state_stack.append(newstate)

        return self.top

    def merge(self) -> ParseState:
        prev = self.pop()
        return self.state.merge(prev)

    def alert(self, level: int = 1, message: str = '') -> Alert:
        self.top.alerts.append(Alert(level=level, message=message))
        return self.top.alerts[-1]

    def __copy__(self) -> ParseStateStack:
        new = self.__class__.__new__(self.__class__)

        new.state_stack = self.state_stack[:]
        new.ruleinfo_stack = self.ruleinfo_stack[:]

        return new
