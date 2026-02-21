# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from itertools import starmap
from typing import Any, NamedTuple, Protocol, runtime_checkable

from ng.ngtokenizing.cursor import Cursor, LineInfo, NullCursor


class LineIndexInfo(NamedTuple):
    filename: str
    line: int

    @staticmethod
    def block_index(name: str, n: int) -> list[LineIndexInfo]:
        return list(starmap(LineIndexInfo, zip(n * [name], range(n), strict=False)))


@runtime_checkable
class Tokenizer(Protocol):
    """Abstract protocol for the source provider."""

    @property
    def text(self) -> str: ...

    @property
    def filename(self) -> str: ...

    @property
    def ignorecase(self) -> bool: ...

    def new_cursor(self, pos: int = 0) -> Cursor: ...

    def next_token(self, cursor: Cursor) -> None: ...

    def match(self, cursor: Cursor, token: str) -> str | None: ...

    def matchre(self, cursor: Cursor, pattern: str) -> str | None: ...

    def posline(self, pos: int) -> int: ...

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


class NullTokenizer(Tokenizer):
    """A no-op implementation of the Tokenizer protocol."""

    def __init__(self, *args: Any, **kwargs: Any): pass

    @property
    def text(self) -> str: return ''

    @property
    def filename(self) -> str: return ''

    @property
    def ignorecase(self) -> bool: return False

    def new_cursor(self, pos: int = 0) -> Cursor:
        return NullCursor()

    def next_token(self, cursor: Cursor) -> None: pass

    def match(self, cursor: Cursor, token: str) -> str | None: return None

    def matchre(self, cursor: Cursor, pattern: str) -> str | None: return None

    def posline(self, pos: int) -> int: return 0

    def lineinfo(self, pos: int) -> LineInfo:
        return LineInfo('', 0, 0, 0, 0, '')

    def get_line(self, n: int | None = None) -> str: return ''

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        return []

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return []
