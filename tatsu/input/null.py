# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Self

from . import LineInfo
from .infos import LineIndexInfo
from .text import Cursor, Text


class NullCursor(Cursor):
    def __init__(self) -> None:
        self.pos = 0
        self.textstr = ''

    def clone(self) -> Self:
        return type(self)()

    @property
    def input(self) -> Text:
        return NullText()

    @property
    def linecount(self) -> int:
        return 1  # note: editor view

    @property
    def source(self) -> str:
        return ''

    @property
    def ignorecase(self) -> bool:
        return False

    @property
    def line(self) -> int:
        return 0

    def goto(self, pos) -> None:
        return

    def move(self, n: int) -> None:
        return

    def atend(self) -> bool:
        return False

    def ateol(self) -> bool:
        return False

    @property
    def current(self) -> str | None:
        return None

    @property
    def token(self):
        return self.current

    def next(self) -> str | None:
        return None

    def next_token(self) -> None:
        return None

    def match(self, token: str) -> str | None:
        return None

    def matchre(self, pattern: str) -> str | None:
        return None

    def is_name(self, s: str) -> bool:
        return False

    def is_name_char(self, c: str | None) -> bool:
        return False

    def lineat(self, pos: int | None = None) -> int:
        return 0

    def lineinfo(self, pos: int | None = None) -> LineInfo:
        return LineInfo('', 0, 0, 0, 0, '')

    def get_line(self, n: int | None = None) -> str:
        return ''

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        return []

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return []

    def lookahead(self) -> str:
        return ''

    def lookahead_pos(self) -> str:
        return ''


class NullText(Text):
    def newcursor(self, pos: int = 0) -> Cursor:
        return NullCursor()

    @property
    def text(self) -> str:
        return ''

    @property
    def source(self) -> str:
        return ''
