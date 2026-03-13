# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from .infos import LineIndexInfo, LineInfo


@runtime_checkable
class Cursor(Protocol):
    pos: int
    text: str

    def clone(self) -> Cursor: ...

    @property
    def tokenizer(self) -> Tokenizer: ...

    @property
    def filename(self) -> str: ...

    @property
    def linecount(self) -> int:  ...

    @property
    def line(self) -> int: ...

    @property
    def current(self) -> str | None: ...

    @property
    def token(self):
        return self.current

    def goto(self, pos) -> None: ...

    def move(self, n: int) -> None: ...

    def atend(self) -> bool: ...

    def ateol(self) -> bool: ...

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


class Tokenizer(ABC):
    def __init__(self, text: Any, /, *args, **kwargs) -> None:
        assert text is None or text is not None

    @abstractmethod
    def newcursor(self) -> Cursor: ...

    @property
    @abstractmethod
    def filename(self) -> str: ...
