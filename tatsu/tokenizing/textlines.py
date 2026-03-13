# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from typing import Any

from ..parserconfig import ParserConfig
from ..util import Undefined, cached_re_compile, notnone, str_from_match, typename
from .infos import LineIndexInfo, LineInfo, PosLine
from .tokenizer import Cursor, Tokenizer

DEFAULT_WHITESPACE_RE = re.compile(r'(?m)\s+')


class TextLinesCursor(Cursor):
    __slots__ = ('len', 'pos', 'tokens')

    def __init__(self, tokens: TextLinesTokenizer, pos: int = 0):
        self.tokens: TextLinesTokenizer = tokens
        self.pos: int = pos
        self.len: int = tokens.len
        self.text = tokens.text

    def clone(self) -> Cursor:
        return TextLinesCursor(self.tokens, self.pos)

    @property
    def tokenizer(self) -> TextLinesTokenizer:
        return self.tokens

    @property
    def line(self) -> int:
        return self.posline(self.pos)

    @property
    def col(self) -> int:
        return self.poscol(self.pos)

    @property
    def filename(self) -> str:
        return self.tokens.filename

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
        return self.text[self.pos]

    def peek(self, n: int = 1) -> str | None:
        p = self.pos + n
        if p >= self.len or p < 0:
            return None
        return self.text[p]

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

    def match(self, token: str) -> str | None:
        if token is None:
            return None

        p = self.pos
        text = self.text[p : p + len(token)]

        if self.tokens.ignorecase:
            is_match = text.lower() == token.lower()
        else:
            is_match = text == token

        if not is_match:
            return None

        self.move(len(token))
        partial_match = (
            self.tokens.nameguard
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
        return c is not None and (c.isalnum() or c in self.tokens._namechar_set)

    def is_name(self, s: str) -> bool:
        if not s:
            return False

        goodstart = s[0].isalpha() or s[0] in self.tokens._namechar_set
        return goodstart and all(self.is_name_char(c) for c in s[1:])

    def lineinfo(self, pos: int | None = None) -> LineInfo:
        pos = notnone(pos, self.pos)
        tokenizer = self.tokens

        if not tokenizer.line_cache or not tokenizer.line_index:
            return LineInfo(tokenizer.filename, 0, 0, 0, tokenizer.len, tokenizer.text)

        # Ensure pos is within bounds for cache lookup
        # The cache has an extra entry at the end, so len - 2 is the last valid index for content
        pos = min(pos, len(tokenizer.line_cache) - 2)
        start, line, length = tokenizer.line_cache[pos]
        end = start + length
        col = pos - start
        text = tokenizer.text[start:end]

        n = min(len(tokenizer.line_index) - 1, line)
        filename, actual_line = tokenizer.line_index[n]
        return LineInfo(filename, actual_line, col, start, end, text)

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
        return self.tokens.split_block_lines(text)[0].rstrip()

    def posline(self, pos: int | None = None) -> int:
        pos = notnone(pos, self.pos)
        if not self.tokens.line_cache:
            return 0
        return self.tokens.line_cache[pos].line

    def poscol(self, pos: int | None = None) -> int:
        pos = notnone(pos, self.pos)
        if not self.tokens.line_cache:
            return 0
        start = self.tokens.line_cache[pos].start
        return pos - start

    def get_line(self, n: int | None = None) -> str:
        return self.tokens.get_line(notnone(n, self.line))

    def get_lines(
        self,
        start: int | None = None,
        end: int | None = None,
    ) -> list[str]:
        return self.tokens.get_lines(start, end)

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return self.tokens.line_index_at(start, end)

    def eat_whitespace(self) -> bool:
        if self.tokens.whitespace_re:
            return self._eat_regex(self.tokens.whitespace_re)
        return False

    def eat_comments(self) -> bool:
        return self._eat_regex(self.tokens.config.comments)

    def eat_eol_comments(self) -> bool:
        return self._eat_regex(self.tokens.config.eol_comments)

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
        return cre.match(self.text, self.pos)

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
        super().__init__(text, config=config)
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
        self.text = ""
        self.lines: list[str] = []
        self.line_index: list[LineIndexInfo] = []
        self.line_cache: list[PosLine] = []

        self._preprocess()
        self._postprocess()

    def newcursor(self) -> Cursor:
        return TextLinesCursor(self)

    @property
    def filename(self) -> str:
        return str(self.config.filename or '')

    @property
    def len(self) -> int:
        return len(self.text)

    @property
    def linecount(self) -> int:
        return len(self.lines)

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
        self.lines = lines
        self.line_index = index
        self.text = self.join_block_lines(lines)

    def _postprocess(self):
        cache, count = PosLine.build_line_cache(self.lines, len(self.text))
        self.line_cache = cache
        self._linecount = count

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
        return self.lines[start : notnone(end, len(self.lines)) + 1]

    def line_index_at(
        self, start: int = 0, end: int | None = None
    ) -> list[LineIndexInfo]:
        if end is None:
            end = len(self.line_index)
        return self.line_index[start : 1 + end]
