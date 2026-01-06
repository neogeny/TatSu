from __future__ import annotations

import dataclasses
from collections.abc import Callable
from itertools import starmap
from typing import Any, NamedTuple

from .ast import AST


class UndefinedStr(str):
    pass


_undefined_str = UndefinedStr('>>undefined<<')


class PosLine(NamedTuple):
    start: int
    line: int
    length: int

    @staticmethod
    def build_line_cache(lines):
        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for _ in line:
                cache.append(pl)  # noqa: PERF401
            i += len(line)
        n += 1
        if lines and lines[-1] and lines[-1][-1] in '\r\n':
            n += 1
        cache.append(PosLine(i, n, 0))
        return cache, n


class LineIndexInfo(NamedTuple):
    filename: str
    line: int

    @staticmethod
    def block_index(name, n):
        return list(
            starmap(LineIndexInfo, zip(n * [name], range(n), strict=False)),
        )


class LineInfo(NamedTuple):
    filename: str
    line: int
    col: int
    start: int
    end: int
    text: str


class CommentInfo(NamedTuple):
    inline: list
    eol: list

    @staticmethod
    def new_comment():
        return CommentInfo([], [])


class Alert(NamedTuple):
    level: int = 1
    message: str = ''


class ParseInfo(NamedTuple):
    tokenizer: Any
    rule: str
    pos: int
    endpos: int
    line: int
    endline: int
    alerts: list[Alert] = []  # noqa: RUF012

    def text_lines(self):
        return self.tokenizer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.tokenizer.line_index(self.line, self.endline)

    @property
    def buffer(self):
        return self.tokenizer


class MemoKey(NamedTuple):
    pos: int
    rule: str
    state: Any


class RuleInfo(NamedTuple):
    name: str
    impl: Callable
    is_leftrec: bool
    is_memoizable: bool
    is_name: bool
    params: list
    kwparams: dict

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class RuleResult(NamedTuple):
    node: Any
    newpos: int
    newstate: Any


@dataclasses.dataclass(slots=True)
class ParseState:
    pos: int = 0
    ast: AST = dataclasses.field(default_factory=AST)
    cst: Any = None
    alerts: list[Alert] = dataclasses.field(default_factory=list)
