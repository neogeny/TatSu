# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from itertools import starmap
from typing import NamedTuple, Protocol, runtime_checkable


class LineIndexInfo(NamedTuple):
    filename: str
    line: int

    @staticmethod
    def block_index(name, n) -> list[LineIndexInfo]:
        return list(starmap(LineIndexInfo, zip(n * [name], range(n), strict=False)))


class LineInfo(NamedTuple):
    filename: str
    line: int
    col: int
    start: int
    end: int
    text: str


@runtime_checkable
class Cursor(Protocol):
    def clonecursor(self) -> Cursor: ...

    @property
    def text(self) -> str: ...

    @property
    def filename(self) -> str: ...

    @property
    def pos(self) -> int: ...

    @property
    def line(self) -> int: ...

    def goto(self, pos) -> None: ...

    def atend(self) -> bool: ...

    def ateol(self) -> bool: ...

    @property
    def current(self) -> str | None: ...

    @property
    def token(self):
        return self.current

    def next(self) -> str | None: ...

    def next_token(self) -> None: ...

    def match(self, token: str) -> str | None: ...

    def matchre(self, pattern: str) -> str | None: ...

    def posline(self, pos: int | None = None) -> int: ...

    def lineinfo(self, pos: int | None = None) -> LineInfo: ...

    def get_line(self, n: int | None = None) -> str: ...

    def get_lines(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> list[str]: ...

    def line_index(
        self,
        start: int = 0,
        end: int | None = None,
    ) -> list[LineIndexInfo]: ...

    def lookahead(self) -> str: ...

    def lookahead_pos(self) -> str: ...
