# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
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
            self.cursor: Cursor = base.cursor.clone()
            self.ast: AST = AST(base.ast)
        else:
            self.cursor = base.clone()
            self.ast = AST()

        self.cst: Any = None
        self.cutseen: bool = False
        self.last_node: Any = None
        self.alerts: list[Alert] = []

    def clone(self) -> Self:
        return type(self)(self)

    def __copy__(self) -> Self:
        new = type(self)(self.cursor)
        new.alerts = self.alerts[:]
        return new

    def merge(self, prev: ParseState) -> Self:
        self.ast = prev.ast
        self.extend(prev.cst)
        self.alerts.extend(prev.alerts)
        self.cursor.goto(prev.cursor.pos)
        return self

    @property
    def node(self) -> Any:
        ast = self.ast
        cst = self.cst
        if not ast:
            return cstfinal(cst)
        elif _AT_ in ast:
            return ast[_AT_]
        else:
            return ast

    def append(self, node: Any) -> Any:
        self.last_node = node
        self.cst = cstadd(self.cst, node)
        return node

    def extend(self, node: Any) -> Any:
        self.last_node = node
        self.cst = cstmerge(self.cst, node)
        return node

    def nameset(self, name: str) -> None:
        self.ast._set(name, self.last_node)

    def nameadd(self, name: str) -> None:
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
        new = type(self)(self.state.cursor)
        new.state_stack = self.state_stack[:]
        new.ruleinfo_stack = self.ruleinfo_stack[:]
        return new

    @property
    def state(self) -> ParseState:
        return self.state_stack[-1]

    @property
    def node(self) -> Any:  # this is Parsed
        return self.state.node

    def undo(self) -> ParseState:
        return self.state_stack.pop()

    def pop(self) -> ParseState:
        prev = self.state_stack.pop()
        self.state.cursor.goto(prev.cursor.pos)
        return prev

    def new(self) -> ParseState:
        newstate = ParseState(self.state.cursor)
        self.state_stack.append(newstate)
        return self.state

    def push(self) -> ParseState:
        newstate = ParseState(self.state)
        self.state_stack.append(newstate)

        return self.state

    def merge(self) -> ParseState:
        prev = self.pop()
        return self.state.merge(prev)

    def alert(self, level: int = 1, message: str = '') -> Alert:
        self.state.alerts.append(Alert(level=level, message=message))
        return self.state.alerts[-1]

    def __copy__(self) -> ParseStateStack:
        new = self.__class__.__new__(self.__class__)

        new.state_stack = self.state_stack[:]
        new.ruleinfo_stack = self.ruleinfo_stack[:]

        return new
