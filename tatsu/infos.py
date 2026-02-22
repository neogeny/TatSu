# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from .parserconfig import ParserConfig  # for backwards compatibility
from .tokenizing import Cursor, PosLine

__all__ = ['Alert', 'ParserConfig', 'ParseInfo', 'PosLine', 'RuleInfo']


class Alert(NamedTuple):
    level: int = 1
    message: str = ''


class ParseInfo(NamedTuple):
    cursor: Cursor
    rule: str
    pos: int
    endpos: int
    line: int
    endline: int
    alerts: list[Alert] = []  # noqa: RUF012

    @property
    def tokenizer(self) -> Cursor:
        # NOTE:
        #   info.tokenizer provided for bakwards compatibility
        #   self.cursor.tokenizer:Tokenizer is opaque, so useless
        return self.cursor

    def text_lines(self) -> list[str]:
        return self.cursor.get_lines(self.line, self.endline)

    def line_index(self):
        return self.cursor.line_index(self.line, self.endline)


class RuleInfo(NamedTuple):
    name: str
    impl: Callable
    is_leftrec: bool
    is_memoizable: bool
    is_name: bool
    params: list[Any] | tuple[Any, ...]
    kwparams: dict[str, Any]

    def is_token_rule(self):
        return self.name.lstrip('_')[:1].isupper()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class CommentInfo(NamedTuple):
    inline: list
    eol: list

    @staticmethod
    def new_comment():
        return CommentInfo([], [])
