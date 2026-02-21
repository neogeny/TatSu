# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ng.ngtokenizing.cursor import Cursor, LineInfo
from ng.ngtokenizing.tokenizer import LineIndexInfo, Tokenizer


class NullCursor(Cursor):
    """A no-op implementation of the Cursor protocol."""

    @property
    def pos(self) -> int:
        return 0

    @property
    def line(self) -> int:
        return 0

    @property
    def col(self) -> int:
        return 0

    def goto(self, pos: int) -> None:
        pass

    def move(self, n: int) -> None:
        pass

    def atend(self) -> bool:
        return True

    def ateol(self) -> bool:
        return True

    @property
    def current(self) -> str | None:
        return None

    def next(self) -> str | None:
        return None

    def next_token(self) -> None:
        return None

    def match(self, token: str) -> str | None:
        return None

    def matchre(self, pattern: str) -> str | None:
        return None

    def lookahead(self) -> str:
        return ''

    def lookahead_pos(self) -> str:
        return ''

    def posline(self, pos: int | None = None) -> int:
        return 0

    def lineinfo(self, pos: int | None = None) -> LineInfo:
        return LineInfo('', 0, 0, 0, 0, '')


class NullTokenizer(Tokenizer):
    """A no-op implementation of the Tokenizer protocol."""

    def __init__(self, *args: Any, **kwargs: Any):
        pass

    @property
    def text(self) -> str:
        return ''

    @property
    def filename(self) -> str:
        return ''

    @property
    def ignorecase(self) -> bool:
        return False

    def new_cursor(self, pos: int = 0) -> Cursor:
        return NullCursor()

    def next_token(self, cursor: Cursor) -> None:
        pass

    def match(self, cursor: Cursor, token: str) -> str | None:
        return None

    def matchre(self, cursor: Cursor, pattern: str) -> str | None:
        return None

    def posline(self, pos: int) -> int:
        return 0

    def lineinfo(self, pos: int) -> LineInfo:
        return LineInfo('', 0, 0, 0, 0, '')

    def get_line(self, n: int | None = None) -> str:
        return ''

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        return []

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return []
