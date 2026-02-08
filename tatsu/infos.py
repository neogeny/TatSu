# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from .parserconfig import ParserConfig
from .tokenizing import Tokenizer

__all__ = ['Alert', 'ParserConfig', 'ParseInfo', 'RuleInfo']


class Alert(NamedTuple):
    level: int = 1
    message: str = ''


class ParseInfo(NamedTuple):
    tokenizer: Tokenizer  # note: a tokenizer ref is the least memory option
    rule: str
    pos: int
    endpos: int
    line: int
    endline: int
    alerts: list[Alert] = []  # noqa: RUF012

    def text_lines(self) -> list[str]:
        return self.tokenizer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.tokenizer.line_index(self.line, self.endline)

    @property
    def buffer(self):
        return self.tokenizer


class RuleInfo(NamedTuple):
    name: str
    impl: Callable
    is_leftrec: bool
    is_memoizable: bool
    is_name: bool
    params: list[Any] | tuple[Any]
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


class PosLine(NamedTuple):
    start: int
    line: int
    length: int

    @staticmethod
    def build_line_cache(lines, size):
        # an index from original positions to PosLine entries
        if not lines:
            return [], 1

        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for _ in line:
                cache.append(pl)  # noqa: PERF401
            i += len(line)

        n += 1
        if lines[-1][-1] in {'\r', '\n'}:
            n += 1
        cache.append(PosLine(i, n, 0))

        # the range depends on line[-1] ending in a newline
        endrange = range(len(lines), 2 + len(lines))
        assert n in endrange
        assert len(cache) == 1 + size

        return cache, n


class CommentInfo(NamedTuple):
    inline: list
    eol: list

    @staticmethod
    def new_comment():
        return CommentInfo([], [])
