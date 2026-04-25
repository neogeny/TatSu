# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from typing import Any, Self

from ..config import ParserConfig
from ..util import (
    Undefined,
    linecount,
    notnone,
    str_from_match,
    typename,
)
from ..util.newlines import take_linebreak_len, take_non_newline_whitespace_len
from ..util.regextools import cached_re_compile
from . import LineInfo
from .infos import LineIndexInfo, PosLine
from .text import Cursor, Text


DEFAULT_WHITESPACE_RE = re.compile(r'(?m)\s+')


class TextLinesCursor(Cursor):
    __slots__ = ('_input', 'len', 'pos', 'textstr')

    def __init__(self, input: TextLines, pos: int = 0):
        self._input: TextLines = input
        self.pos: int = pos
        self.len: int = input.len
        self.textstr = input.textstr

    def clone(self) -> Self:
        return type(self)(self.input, pos=self.pos)

    def __copy__(self) -> Self:
        return type(self)(self.input, pos=self.pos)

    @property
    def input(self) -> TextLines:
        return self._input

    @property
    def line(self) -> int:
        return self.lineat(self.pos)

    @property
    def linecount(self) -> int:
        return self.input.linecount

    @property
    def col(self) -> int:
        return self.poscol(self.pos)

    @property
    def source(self) -> str:
        n = min(len(self.input.line_index) - 1, self.line)
        source, _actual_line = self.input.line_index[n]
        return source

    def goto(self, pos: int):
        self.pos = max(0, min(self.len, pos))

    def move(self, n: int):
        self.goto(self.pos + n)

    def atend(self) -> bool:
        return self.pos >= self.len

    def ateol(self) -> bool:
        return self.atend() or self.current in {'\r', '\n', None}

    @property
    def current(self) -> str | None:
        if self.pos >= self.len:
            return None
        return self.textstr[self.pos]

    def peek(self, n: int = 1) -> str | None:
        p = self.pos + n
        if p >= self.len or p < 0:
            return None
        return self.textstr[p]

    def next(self) -> str | None:
        if self.atend():
            return None
        c = self.current
        self.move(1)
        return c

    def next_token(self) -> None:
        p = None
        while self.pos != p:
            p = self.pos
            self.eat_whitespace()
            if self.eat_eol_comments():
                self.eat_whitespace()
            self.eat_comments()

    def eat_spaces_no_newlines(self):
        p = None
        while self.pos != p:
            p = self.pos
            self.pos += take_non_newline_whitespace_len(self.textstr, self.pos)
            if self.eat_eol_comments():
                self.pos += take_non_newline_whitespace_len(self.textstr, self.pos)
            self.eat_comments()

    def matcheol(self) -> bool:
        mark = self.pos
        self.eat_spaces_no_newlines()
        eol_len = take_linebreak_len(self.textstr, self.pos)
        if eol_len is None:
            self.pos = mark
            return False
        self.move(eol_len)
        self.eat_spaces_no_newlines()
        return True

    def match(self, token: str) -> str | None:
        if not token:
            return None

        p = self.pos
        text = self.textstr[p : p + len(token)]

        if self.input.ignorecase:
            is_match = text.lower() == token.lower()
        else:
            is_match = text == token

        if not is_match:
            return None

        self.move(len(token))
        partial_match = (
            self.input.nameguard
            and self.is_name_char(self.current)
            and self.is_name(token)
        )
        if partial_match:
            self.goto(p)
            return None

        return token

    def matchre(self, pattern: str | re.Pattern) -> str | None:
        if not (match := self._scanre(pattern)):
            return None
        matched = match.group()
        token = str_from_match(match)
        self.move(len(matched))
        return token

    def is_name_char(self, c: str | None) -> bool:
        return c is not None and (c.isalnum() or c in self.input._namechar_set)

    def is_name(self, s: str) -> bool:
        if not s:
            return False

        goodstart = s[0].isalpha() or s[0] in self.input._namechar_set
        return goodstart and all(self.is_name_char(c) for c in s[1:])

    def lineinfo(self, pos: int | None = None) -> LineInfo:
        pos = notnone(pos, self.pos) or 0
        input = self.input

        if not input.line_cache or not input.line_index:
            return LineInfo(
                source=input.source,
                line=0,
                col=0,
                start=0,
                end=input.len,
                text=input.textstr,
            )

        # Ensure start is within bounds for cache lookup
        # The cache has an extra entry at the end, so len - 2 is the last valid index for content
        pos = min(pos, len(input.line_cache) - 2)
        start, line, length = input.line_cache[pos]
        end = start + length
        col = pos - start
        text = input.textstr[start:end]

        n = min(len(input.line_index) - 1, line)
        source, actual_line = input.line_index[n]
        return LineInfo(
            source=source,
            line=actual_line,
            col=col,
            start=start,
            end=end,
            text=text,
        )

    def lookahead_pos(self) -> str:
        if self.atend():
            return ''
        info = self.lineinfo(self.pos)
        return '@%d:%d' % (info.line + 1, info.col + 1)

    def lookahead(self) -> str:
        if self.atend():
            return ''
        info = self.lineinfo(self.pos)
        text = info.text[info.col : info.col + 1 + 80]
        return self.input.split_block_lines(text)[0].rstrip()

    def lineat(self, pos: int | None = None) -> int:
        pos = notnone(pos, self.pos) or 0
        if not self.input.line_cache:
            return 0
        return self.input.line_cache[pos].lineno

    def poscol(self, pos: int | None = None) -> int:
        pos = notnone(pos, self.pos) or 0
        if not self.input.line_cache:
            return 0
        start = self.input.line_cache[pos].startpos
        return pos - start

    def get_line(self, n: int | None = None) -> str:
        return self.input.get_line(notnone(n, self.line))

    def get_lines(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> list[str]:
        return self.input.get_lines(start, end)

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return self.input.line_index_at(start, end)

    def eat_whitespace(self) -> bool:
        if self.input.whitespace_re:
            return self._eat_regex(self.input.whitespace_re)
        return False

    def eat_comments(self) -> bool:
        return self._eat_regex(self.input.config.comments)

    def eat_eol_comments(self) -> bool:
        return self._eat_regex(self.input.config.eol_comments)

    def _eat_regex(self, regex: str | re.Pattern | None) -> bool:
        if not regex:
            return False
        res = False
        while self._matchre_fast(regex):
            res = True
        return res

    def _matchre_fast(self, pattern: str | re.Pattern | None) -> bool:
        if not (match := self._scanre(pattern)):
            return False
        self.move(len(match.group()))
        return True

    def _scanre(self, pattern: str | re.Pattern | None) -> re.Match[Any] | None:
        if not (cre := cached_re_compile(pattern)):
            return None
        return cre.match(self.textstr, self.pos)

    def __len__(self) -> int:
        return self.len

    def __repr__(self) -> str:
        pos = self.pos
        return f'{typename(self)}({pos=})'


class TextLines(Text):
    def __init__(
        self,
        text: str,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
    ):
        config = ParserConfig.new(config=config, **settings)
        assert isinstance(config, ParserConfig)
        self.config = config

        text = str(text)
        self.original_text = text

        self.whitespace_re = self.build_whitespace_re(config.whitespace)
        self.nameguard = (
            config.nameguard
            if config.nameguard is not None
            else bool(self.whitespace_re) or bool(config.namechars)
        )
        self._namechar_set = set(config.namechars or '')

        # Structural data
        self.textstr = ""
        self.lines: list[str] = []
        self.line_index: list[LineIndexInfo] = []
        self.line_cache: list[PosLine] = []

        self._preprocess()
        self._postprocess()

    def newcursor(self) -> Cursor:
        return TextLinesCursor(self)

    @property
    def source(self) -> str:
        return str(self.config.source or '')

    @property
    def len(self) -> int:
        return len(self.textstr)

    @property
    def linecount(self) -> int:
        return linecount(self.textstr)

    @property
    def ignorecase(self) -> bool:
        return bool(self.config.ignorecase)

    @staticmethod
    def build_whitespace_re(whitespace: Any) -> re.Pattern | None:
        if whitespace is Undefined:
            return DEFAULT_WHITESPACE_RE
        if whitespace in {None, ''}:
            return None
        if isinstance(whitespace, re.Pattern):
            return whitespace
        if whitespace:
            return cached_re_compile(whitespace)
        return None

    def _preprocess(self):
        lines, index = self._preprocess_block(self.source, self.original_text)
        self.lines = lines
        self.line_index = index
        self.textstr = self.join_block_lines(lines)

    def _postprocess(self):
        cache, _count = PosLine.build_line_cache(self.lines, len(self.textstr))
        self.line_cache = cache

    def _preprocess_block(
        self,
        name: str,
        block: str,
        **kwargs,
    ) -> tuple[list[str], list[LineIndexInfo]]:
        lines = self.split_block_lines(block)
        index = LineIndexInfo.block_index(name, len(lines))
        return self.process_block(name, lines, index, **kwargs)

    def split_block_lines(self, block: str) -> list[str]:
        return block.splitlines(True)

    def join_block_lines(self, lines: list[str]) -> str:
        return ''.join(lines)

    def process_block(
        self,
        _name: str,
        lines: list[str],
        index: list[LineIndexInfo],
        **_kwargs,
    ):
        return lines, index

    def get_line(self, n: int) -> str:
        return self.lines[n]

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        if start is None:
            start = 0
        return self.lines[start : notnone(end, start + 1)]

    def line_index_at(
        self, start: int = 0, end: int | None = None
    ) -> list[LineIndexInfo]:
        if end is None:
            end = len(self.line_index)
        return self.line_index[start : 1 + end]


TextLinesTokenizer = TextLines
