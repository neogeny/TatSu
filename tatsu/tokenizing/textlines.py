# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from typing import Any

from .cursor import Cursor, LineIndexInfo, LineInfo
from .infos import PosLine
from .tokenizer import Tokenizer
from ..parserconfig import ParserConfig
from ..util.common import typename
from ..util.itertools import str_from_match
from ..util.misc import cached_re_compile
from ..util.undefined import Undefined

DEFAULT_WHITESPACE_RE = re.compile(r'(?m)\s+')


class PositionCursor(Cursor):
    def __init__(self, tokens: TextLinesTokenizer, pos: int = 0):
        super().__init__()
        self._tokens = tokens
        self._pos = pos
        self._len = tokens._len

    def clonecursor(self) -> Cursor:
        return PositionCursor(self.tokens, self.pos)

    @property
    def tokens(self) -> TextLinesTokenizer:
        return self._tokens

    @property
    def tokenizer(self) -> TextLinesTokenizer:
        return self._tokens

    @property
    def pos(self) -> int:
        return self._pos

    @property
    def len(self) -> int:
        return self._len

    @pos.setter
    def pos(self, p: int):
        self.goto(p)

    @property
    def line(self) -> int:
        return self.tokens.posline(self.pos)

    @property
    def col(self) -> int:
        return self.tokens.poscol(self.pos)

    @property
    def text(self) -> str:
        return self.tokens.text

    @property
    def filename(self) -> str:
        return self.tokens.filename

    def goto(self, pos: int):
        self._pos = max(0, min(self.tokens._len, pos))

    def move(self, n: int):
        self.goto(self._pos + n)

    def atend(self) -> bool:
        return self._pos >= self.len

    def ateol(self) -> bool:
        return self.atend() or self.current in {'\r', '\n', None}

    @property
    def current(self) -> str | None:
        if self.pos >= self.len:
            return None
        return self.text[self._pos]

    def peek(self, n: int = 1) -> str | None:
        p = self.pos + n
        if p >= self.len or p < 0:
            return None
        return self.tokens.text[p]

    def next(self) -> str | None:
        if self.atend():
            return None
        c = self.current
        self.move(1)
        return c

    def next_token(self) -> None:
        self.tokens.next_token(self)

    def match(self, token: str) -> str | None:
        return self.tokens.match(self, token)

    def matchre(self, pattern: str) -> str | None:
        return self.tokens.matchre(self, pattern)

    def lineinfo(self, pos: int | None = None) -> LineInfo:
        if pos is None:
            pos = self.pos
        return self.tokens.lineinfo(pos)

    def lookahead_pos(self) -> str:
        if self.atend():
            return ''
        info = self.tokens.lineinfo(self._pos)
        return '@%d:%d' % (info.line + 1, info.col + 1)

    def lookahead(self) -> str:
        if self.atend():
            return ''
        info = self.tokens.lineinfo(self._pos)
        text = info.text[info.col: info.col + 1 + 80]
        return self.tokens.split_block_lines(text)[0].rstrip()

    def posline(self, pos: int | None = None) -> int:
        if pos is None:
            pos = self.pos
        return self.tokens.posline(pos)

    def get_line(self, n: int | None = None) -> str:
        if n is None:
            n = self.line
        return self.tokens.get_line(n)

    def get_lines(
        self,
        start: int | None = None,
        end: int | None = None,
        ) -> list[str]:
        return self.tokens.get_lines(start, end)

    def line_index(
        self,
        start: int = 0,
        end: int | None = None,
        ) -> list[LineIndexInfo]:
        return self.tokens.line_index(start, end)

    def __len__(self) -> int:
        return self.len

    def __repr__(self) -> str:
        pos = self.pos
        return f'{typename(self)}({pos=})'


class TextLinesTokenizer(Tokenizer):
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

    def newcursor(self, pos: int = 0) -> Cursor:
        """Factory method to create a cursor for this buffer."""
        return PositionCursor(self, pos)

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
        name: str,
        lines: list[str],
        index: list[LineIndexInfo],
        **kwargs,
        ):
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

    def _eat_regex_list(
        self,
        cursor: Cursor,
        regex: str | re.Pattern | None,
        ) -> list[str]:
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
            self.nameguard and self.is_name_char(cursor.current) and self.is_name(token)
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

    def _scanre(
        self,
        cursor: Cursor,
        pattern: str | re.Pattern | None,
        ) -> re.Match[Any] | None:
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

    def get_line(self, n: int) -> str:
        return self._lines[n]

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        if start is None:
            start = 0
        if end is None:
            end = len(self._lines)
        return self._lines[start: end + 1]

    def is_name_char(self, c: str | None) -> bool:
        return c is not None and (c.isalnum() or c in self._namechar_set)

    def is_name(self, s: str) -> bool:
        if not s:
            return False

        goodstart = s[0].isalpha() or s[0] in self._namechar_set
        return goodstart and all(self.is_name_char(c) for c in s[1:])
