# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from functools import cached_property
from typing import Protocol, Self, runtime_checkable

from .infos import LineInfo


@runtime_checkable
class Cursor(Protocol):
    pos: int
    textstr: str

    def clone(self) -> Self: ...

    @property
    def input(self) -> Text: ...

    @property
    def source(self) -> str: ...

    @property
    def linecount(self) -> int: ...

    @property
    def line(self) -> int: ...

    @property
    def current(self) -> str | None: ...

    @property
    def token(self):
        return self.current

    @cached_property
    def namechars(self) -> set[str]: ...

    def goto(self, pos) -> None: ...
    def move(self, n: int) -> None: ...
    def atend(self) -> bool: ...
    def ateol(self) -> bool: ...
    def next(self) -> str | None: ...

    def next_token(self) -> None: ...
    def match(self, token: str) -> str | None: ...
    def matchre(self, pattern: str) -> str | None: ...
    def matcheol(self) -> bool: ...
    def matchname(self) -> str | None: ...

    def is_name(self, s: str) -> bool: ...
    def is_name_char(self, c: str | None) -> bool: ...

    def lineat(self, pos: int | None = None) -> int: ...
    def lineinfo(self, pos: int | None = None) -> LineInfo: ...

    def lookahead(self) -> str: ...
    def lookahead_pos(self) -> str: ...


@runtime_checkable
class Text(Protocol):
    def newcursor(self) -> Cursor: ...

    @property
    def source(self) -> str: ...


Tokenizer = Text


def match_name(s: str, pos: int, namechars: set[str]) -> int:
    if not s or pos < 0 or pos >= len(s):
        return -1

    p = pos
    is_name_start = (c := s[p]) and (c.isalpha() or c in namechars)
    if not is_name_start:
        return -1
    p += 1

    while p < len(s) and (c := s[p]) and (c.isalnum() or c in namechars):
        p += 1

    return p


def matchname(c: Cursor) -> str | None:
    if c.atend():
        return None

    s = c.textstr
    i = c.pos
    p = match_name(s, c.pos, c.namechars)
    if p > 0:
        c.goto(p)
        return s[i:p]
    return None
