# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import NamedTuple, Protocol, runtime_checkable


class LineInfo(NamedTuple):
    filename: str
    line: int
    col: int
    start: int
    end: int
    text: str


@runtime_checkable
class Cursor(Protocol):
    """Abstract protocol for navigation state within a Tokenizer."""

    @property
    def pos(self) -> int: ...

    @property
    def line(self) -> int: ...

    @property
    def col(self) -> int: ...

    def goto(self, pos: int) -> None: ...

    def move(self, n: int) -> None: ...

    def atend(self) -> bool: ...

    def ateol(self) -> bool: ...

    @property
    def current(self) -> str | None: ...

    def next(self) -> str | None: ...

    def next_token(self) -> None: ...

    def match(self, token: str) -> str | None: ...

    def matchre(self, pattern: str) -> str | None: ...

    def lookahead(self) -> str: ...

    def lookahead_pos(self) -> str: ...

    def posline(self, pos: int | None = None) -> int: ...

    def lineinfo(self, pos: int) -> LineInfo: ...
