# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from typing import Any

from ..infos import ParserConfig, PosLine
from ..tokenizing import LineIndexInfo, LineInfo, Tokenizer
from ..util.itertools import str_from_match
from ..util.misc import cached_re_compile
from ..util.undefined import Undefined

DEFAULT_WHITESPACE_RE = re.compile(r'(?m)\s+')
LineIndexEntry = LineIndexInfo


class Cursor:
    """Manages the state and navigation within a Buffer."""

    def __init__(self, buffer: Buffer, pos: int = 0):
        self.buffer = buffer
        self._pos = 0
        self.goto(pos)

    @property
    def pos(self) -> int:
        return self._pos

    @pos.setter
    def pos(self, p: int):
        self.goto(p)

    def goto(self, pos: int):
        self._pos = max(0, min(self.buffer._len, pos))

    def move(self, n: int):
        self.goto(self._pos + n)

    @property
    def line(self) -> int:
        return self.buffer.posline(self._pos)

    @property
    def col(self) -> int:
        return self.buffer.poscol(self._pos)

    def atend(self) -> bool:
        return self._pos >= self.buffer._len

    def ateol(self) -> bool:
        return self.atend() or self.current in {'\r', '\n', None}

    @property
    def current(self) -> str | None:
        if self._pos >= self.buffer._len:
            return None
        return self.buffer.text[self._pos]

    def peek(self, n: int = 1) -> str | None:
        p = self._pos + n
        if p >= self.buffer._len or p < 0:
            return None
        return self.buffer.text[p]

    def next(self) -> str | None:
        if self.atend():
            return None
        c = self.current
        self.move(1)
        return c

    def lookahead_pos(self) -> str:
        if self.atend():
            return ''
        info = self.buffer.lineinfo(self._pos)
        return '@%d:%d' % (info.line + 1, info.col + 1)

    def lookahead(self) -> str:
        if self.atend():
            return ''
        info = self.buffer.lineinfo(self._pos)
        text = info.text[info.col: info.col + 1 + 80]
        return self.buffer.split_block_lines(text)[0].rstrip()

    def __repr__(self) -> str:
        return f'Cursor(pos={self._pos}, line={self.line}, col={self.col})'


class Buffer(Tokenizer):
    def __init__(
        self,
        text: str,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
        ):
        config = ParserConfig.new(config=config, **settings)
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
        self._text = ""
        self._len = 0
        self._linecount = 0
        self._lines: list[str] = []
        self._line_index: list[LineIndexInfo] = []
        self._line_cache: list[PosLine] = []

        self._preprocess()
        self._postprocess()

    def new_cursor(self, pos: int = 0) -> Cursor:
        """Factory method to create a cursor for this buffer."""
        return Cursor(self, pos)

    @property
    def text(self) -> str:
        return self._text

    @property
    def filename(self) -> str:
        return str(self.config.filename or '')

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
        lines, index = self._preprocess_block(self.filename, self.original_text)
        self._lines = lines
        self._line_index = index
        self._text = self.join_block_lines(lines)

    def _postprocess(self):
        cache, count = PosLine.build_line_cache(self._lines, len(self._text))
        self._line_cache = cache
        self._linecount = count
        self._len = len(self._text)

    def _preprocess_block(self, name: str, block: str, **kwargs) -> tuple[list[str], list[LineIndexInfo]]:
        lines = self.split_block_lines(block)
        index = LineIndexInfo.block_index(name, len(lines))
        return self.process_block(name, lines, index, **kwargs)

    def split_block_lines(self, block: str) -> list[str]:
        return block.splitlines(True)

    def join_block_lines(self, lines: list[str]) -> str:
        return ''.join(lines)

    def process_block(self, name: str, lines: list[str], index: list[LineIndexInfo], **kwargs):
        return lines, index

    # Mapping methods that now take a Cursor instead of using self._pos
    def posline(self, pos: int) -> int:
        return self._line_cache[pos].line

    def poscol(self, pos: int) -> int:
        start = self._line_cache[pos].start
        return pos - start

    def eat_whitespace(self, cursor: Cursor) -> None:
        if self.whitespace_re:
            self._eat_regex(cursor, self.whitespace_re)

    def _eat_regex(self, cursor: Cursor, regex: str | re.Pattern) -> None:
        if not regex:
            return
        while self._matchre_fast(cursor, regex):
            pass

    def next_token(self, cursor: Cursor) -> None:
        p = -1
        while cursor.pos != p:
            p = cursor.pos
            self._eat_regex_list(cursor, self.config.eol_comments)
            self._eat_regex_list(cursor, self.config.comments)
            self.eat_whitespace(cursor)

    def _eat_regex_list(self, cursor: Cursor, regex: str | re.Pattern | None) -> list[str]:
        if not (r := cached_re_compile(regex)):
            return []

        found = []
        while x := self.matchre(cursor, r):
            found.append(x)
        return found

    def match(self, cursor: Cursor, token: str) -> str | None:
        if token is None:
            return None

        p = cursor.pos
        text = self.text[p: p + len(token)]

        if self.ignorecase:
            is_match = text.lower() == token.lower()
        else:
            is_match = text == token

        if not is_match:
            return None

        cursor.move(len(token))
        partial_match = (
            self.nameguard and
            self.is_name_char(cursor.current) and
            self.is_name(token)
        )
        if partial_match:
            cursor.goto(p)
            return None

        return token

    def _matchre_fast(self, cursor: Cursor, pattern: str | re.Pattern | None) -> bool:
        if not (match := self._scanre(cursor, pattern)):
            return False
        cursor.move(len(match.group()))
        return True

    def matchre(self, cursor: Cursor, pattern: str | re.Pattern) -> str | None:
        if not (match := self._scanre(cursor, pattern)):
            return None
        matched = match.group()
        token = str_from_match(match)
        cursor.move(len(matched))
        return token

    def _scanre(self, cursor: Cursor, pattern: str | re.Pattern | None) -> re.Match[Any] | None:
        if not (cre := cached_re_compile(pattern)):
            return None
        return cre.match(self.text, cursor.pos)

    def lineinfo(self, pos: int) -> LineInfo:
        if not self._line_cache or not self._line_index:
            return LineInfo(self.filename, 0, 0, 0, self._len, self.text)

        pos = min(pos, len(self._line_cache) - 2)
        start, line, length = self._line_cache[pos]
        end = start + length
        col = pos - start
        text = self.text[start:end]

        n = min(len(self._line_index) - 1, line)
        filename, actual_line = self._line_index[n]
        return LineInfo(filename, actual_line, col, start, end, text)

    def is_name_char(self, c: str | None) -> bool:
        return c is not None and (c.isalnum() or c in self._namechar_set)

    def is_name(self, s: str) -> bool:
        if not s:
            return False
        goodstart = s[0].isalpha() or s[0] in self._namechar_set
        return goodstart and all(self.is_name_char(c) for c in s[1:])
