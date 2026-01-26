from __future__ import annotations

from typing import Any, Self

from ..infos import Alert

__all__ = [
    'ParseState',
    'ParseStateStack',
]


class ParseState:
    __slots__ = ('alerts', 'ast', 'cst', 'pos')

    def __init__(self, pos: int = 0, ast: Any = None, cst: Any = None):
        self.pos: int = pos
        self.ast: Any = ast
        self.cst: Any = cst
        self.alerts: list[Alert] = []


class ParseStateStack:
    def __init__(self: Self) -> None:
        self._state_stack: list[ParseState] = [ParseState()]

    def top(self) -> ParseState:
        return self._state_stack[-1]

    def pop(self) -> ParseState:
        return self._state_stack.pop()

    def push(self, pos: int = 0, ast: Any = None, cst: Any = None) -> ParseState:
        self._state_stack.append(ParseState(pos=pos, ast=ast, cst=cst))
        return self.top()

    def alert(self, level: int = 1, message: str = '') -> Alert:
        self.top().alerts.append(Alert(level=level, message=message))
        return self.top().alerts[-1]
