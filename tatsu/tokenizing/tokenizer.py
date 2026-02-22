# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Protocol, runtime_checkable

from tatsu.tokenizing import LineIndexInfo, LineInfo


@runtime_checkable
class Cursor(Protocol):
    def clonecursor(self) -> Cursor: ...

    @property
    def tokenizer(self) -> Tokenizer: ...

    @property
    def text(self) -> str: ...

    @property
    def filename(self) -> str: ...

    @property
    def pos(self) -> int: ...

    @property
    def line(self) -> int: ...

    def goto(self, pos) -> None: ...

    def move(self, n: int) -> None: ...

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


class NullCursor(Cursor):
    def clonecursor(self) -> Cursor:
        return NullCursor()

    @property
    def tokenizer(self) -> Tokenizer:
        return NullTokenizer()

    @property
    def text(self) -> str:
        return ''

    @property
    def filename(self) -> str:
        return ''

    @property
    def ignorecase(self) -> bool:
        return False

    @property
    def pos(self) -> int:
        return 0

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

    def posline(self, pos: int | None = None) -> int:
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


@runtime_checkable
class Tokenizer(Protocol):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def newcursor(self) -> Cursor: ...

    # FIXME: this interface is not needed
    # def eat_whitespace_at(self, c: Cursor) -> None: ...
    #
    # def eat_comments_at(self, c: Cursor) -> None: ...
    #
    # def eat_eol_comments_at(self, c: Cursor) -> None: ...
    #
    # def next_token_at(self, c: Cursor) -> None: ...
    #
    # def match_at(self, token: str, c: Cursor) -> str | None: ...
    #
    # def matchre_at(self, pattern: str | re.Pattern, c: Cursor) -> str | None: ...
    #
    # def posline_at(self, pos: int) -> int: ...
    #
    # def poscol_at(self, pos: int) -> int: ...
    #
    # def lineinfo_at(self, pos: int) -> LineInfo: ...
    #
    # def line_index_at(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]: ...


class NullTokenizer(Tokenizer):
    def newcursor(self, pos: int = 0) -> Cursor:
        return NullCursor()

    # FIXME: this interface is not needed
    # def eat_whitespace_at(self, c: Cursor) -> None:
    #     return
    #
    # def eat_comments_at(self, c: Cursor) -> None:
    #     return
    #
    # def eat_eol_comments_at(self, c: Cursor) -> None:
    #     return
    #
    # def next_token_at(self, c: Cursor) -> None:
    #     return
    #
    # def match_at(self, token: str, c: Cursor) -> str | None:
    #     return
    #
    # def matchre_at(self, pattern: str | re.Pattern, c: Cursor) -> str | None:
    #     return
    #
    # def posline_at(self, pos: int) -> int:
    #     return 0
    #
    # def poscol_at(self, pos: int) -> int:
    #     return 0
    #
    # def lineinfo_at(self, pos: int) -> LineInfo:
    #     return LineInfo('', 0, 0, 0, 0, '')
    #
    # def line_index_at(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
    #     return []
