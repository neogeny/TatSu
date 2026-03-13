# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from .infos import LineIndexInfo, LineInfo


@runtime_checkable
class Cursor(Protocol):
    pos: int

    def clone(self) -> Cursor: ...

    @property
    def tokenizer(self) -> Tokenizer: ...

    @property
    def text(self) -> str: ...

    @property
    def filename(self) -> str: ...

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

    def is_name(self, s: str) -> bool: ...

    def is_name_char(self, c: str | None) -> bool: ...

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
    def clone(self) -> Cursor:
        return self

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

    def is_name(self, s: str) -> bool:
        return False

    def is_name_char(self, c: str | None) -> bool:
        return False

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


class Tokenizer(ABC):
    def __init__(self, text: Any, /, *args, **kwargs) -> None:
        assert text is None or text is not None

    @abstractmethod
    def newcursor(self) -> Cursor: ...

    @property
    @abstractmethod
    def filename(self) -> str: ...


class NullTokenizer(Tokenizer):
    def __init__(self) -> None:
        super().__init__(None)

    def newcursor(self, pos: int = 0) -> Cursor:
        return NullCursor()

    @property
    def filename(self) -> str:
        return ''
