# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
The Buffer class provides the functionality required by a parser-driven lexer.

Line analysis and caching are done so the parser can freely move with goto(p)
to any position in the parsed text, and still recover accurate information
about source lines and content.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .infos import PosLine
from .parserconfig import ParserConfig
from .tokenizing import Cursor, LineIndexInfo, LineInfo
from .tokenizing.tokenizer import Tokenizer
from .util.itertools import str_from_match
from .util.misc import cached_re_compile
from .util.undefined import Undefined

DEFAULT_WHITESPACE_RE = re.compile(r'(?m)\s+')

# for backwards compatibility with existing parsers
LineIndexEntry = LineIndexInfo


class Buffer(Cursor, Tokenizer):

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
        self._text = self.original_text = text

        self.whitespace_re = self.build_whitespace_re(config.whitespace)
        self.nameguard = (
            config.nameguard
            if config.nameguard is not None
            else bool(self.whitespace_re) or bool(config.namechars)
        )
        self._namechar_set = set(config.namechars or '')

        self._pos = 0
        self._len = 0
        self._linecount = 0
        self._lines: list[str] = []
        self._line_index: list[LineIndexInfo] = []
        self._line_cache: list[PosLine] = []

        self._preprocess()
        self._postprocess()

    def newcursor(self) -> Cursor:
        return self

    def clonecursor(self) -> Cursor:
        return self

    def lastcursor(self) -> Cursor:
        return self

    @property
    def tokenizer(self) -> Tokenizer:
        return self

    @property
    def text(self) -> str:
        return self._text

    @property
    def filename(self) -> str:
        return str(self.config.filename or '')

    @property
    def ignorecase(self) -> bool:
        return bool(self.config.ignorecase)

    @property
    def whitespace(self) -> str | None:
        return self.config.whitespace

    @staticmethod
    def build_whitespace_re(whitespace: Any) -> re.Pattern | None:
        if whitespace is Undefined:
            return DEFAULT_WHITESPACE_RE
        if whitespace in {None, ''}:
            return None
        elif isinstance(whitespace, re.Pattern):
            return whitespace
        elif whitespace:
            return cached_re_compile(whitespace)
        else:
            return None

    def _preprocess(self, /, *_args: Any, **_kwargs: Any):
        lines, index = self._preprocess_block(self.filename, self.text)
        self._lines = lines
        self._line_index = index
        self._text = self.join_block_lines(lines)

    def _postprocess(self):
        cache, count = PosLine.build_line_cache(self._lines, len(self.text))
        self._line_cache = cache
        self._linecount = count
        self._len = len(self.text)

    def _preprocess_block(
        self,
        name: str,
        block,
        /,
        **kwargs,
        ) -> tuple[list[str], list[LineIndexInfo]]:
        lines = self.split_block_lines(block)
        index = LineIndexInfo.block_index(name, len(lines))
        return self.process_block(name, lines, index, **kwargs)

    def split_block_lines(self, block: str) -> list[str]:
        return block.splitlines(True)

    def join_block_lines(self, lines: list[str]):
        return ''.join(lines)

    def process_block(
        self,
        name: str,
        lines: list[str],
        index: list[LineIndexInfo],
        /,
        **kwargs,
        ) -> tuple[list[str], list[LineIndexInfo]]:
        return lines, index

    def include(
        self,
        lines: list[str],
        index: list[LineIndexInfo],
        i: int,
        j: int,
        name: str,
        block: str,
        /,
        **kwargs,
        ) -> int:
        blines, bindex = self._preprocess_block(name, block, **kwargs)
        assert len(blines) == len(bindex)
        lines[i:j] = blines
        index[i:j] = bindex
        assert len(lines) == len(index)
        return j + len(blines) - 1

    def include_file(
        self,
        source: str,
        name: str,
        lines: list[str],
        index: list[LineIndexInfo],
        i: int,
        j: int,
        ) -> int:
        text, filename = self.get_include(source, name)
        return self.include(lines, index, i, j, filename, text)

    def get_include(self, source: str, filename: str) -> tuple[str, str]:
        source_path = Path(source).resolve()
        base = source_path.parent
        include = base / filename
        try:
            return include.read_text(), str(include)
        except OSError as e:
            raise ValueError(f'include not found: {include}') from e

    def replace_lines(self, i: int, j: int, name: str, block: str) -> tuple[int, str]:
        lines = self.split_block_lines(self.text)
        index = self._line_index

        endline = self.include(lines, index, i, j, name, block)

        self._text = self.join_block_lines(lines)
        self._line_index = index
        self._postprocess()

        newtext = self.join_block_lines(lines[j + 1 : endline + 2])
        return endline, newtext

    @property
    def pos(self) -> int:
        return self._pos

    @pos.setter
    def pos(self, p: int):
        self.goto(p)

    @property
    def line(self) -> int:
        return self.posline()

    @property
    def col(self) -> int:
        return self.poscol()

    def posline(self, pos: int | None = None) -> int:
        if pos is None:
            pos = self._pos
        return self._line_cache[pos].line

    def poscol(self, pos: int | None = None) -> int:
        if pos is None:
            pos = self._pos
        start = self._line_cache[pos].start
        return pos - start

    def atend(self) -> bool:
        return self._pos >= self._len

    def ateol(self) -> bool:
        return self.atend() or self.current in {'\r', '\n', None}

    @property
    def current(self) -> str | None:
        if self._pos >= self._len:
            return None
        return self.text[self._pos]

    def at(self, p: int) -> str | None:
        if p >= self._len:
            return None
        return self.text[p]

    def peek(self, n: int = 1) -> str | None:
        return self.at(self._pos + n)

    def next(self) -> str | None:
        if self.atend():
            return None
        c = self.text[self.pos]
        self.move(1)
        return c

    def goto(self, pos: int):
        self._pos = max(0, min(len(self.text), pos))

    def move(self, n: int):
        self.goto(self.pos + n)

    def _eat_regex(self, regex: str | re.Pattern | None) -> None:
        if not regex:
            return
        while self._matchre_fast(regex):
            pass

    def _eat_regex_list(self, regex: str | re.Pattern | None) -> list[str]:
        if not regex:
            return []

        r = cached_re_compile(regex)
        if r is None:
            return []

        def takewhile_repeat_regex():
            while x := self.matchre(r):
                yield x

        return list(takewhile_repeat_regex())

    def eat_whitespace(self) -> None:
        if self.whitespace_re:
            self._eat_regex(self.whitespace_re)

    def eat_comments(self) -> list[str]:
        return self._eat_regex_list(self.config.comments)

    def eat_eol_comments(self) -> list[str]:
        return self._eat_regex_list(self.config.eol_comments)

    def next_token(self) -> None:
        p = None
        while self._pos != p:
            p = self._pos
            self.eat_eol_comments()
            self.eat_comments()
            self.eat_whitespace()

    def skip_to(self, c: str) -> int:
        p = self._pos
        le = self._len
        while p < le and self.text[p] != c:
            p += 1
        self.goto(p)
        return self.pos

    def skip_past(self, c: str) -> int:
        self.skip_to(c)
        self.next()
        return self.pos

    def skip_to_eol(self) -> int:
        return self.skip_to('\n')

    def scan_space(self) -> bool:
        return bool(self.whitespace_re) and bool(self._scanre(self.whitespace_re))

    def is_space(self) -> bool:
        return self.scan_space()

    def is_name_char(self, c: str | None) -> bool:
        return c is not None and (c.isalnum() or c in self._namechar_set)

    def is_name(self, s: str) -> bool:
        if not s:
            return False
        goodstart = s[0].isalpha() or s[0] in self._namechar_set
        return goodstart and all(self.is_name_char(c) for c in s[1:])

    def match(self, token: str) -> str | None:
        if token is None:
            return None

        p = self.pos
        text = self.text[p : p + len(token)]
        if self.ignorecase:
            is_match = text.lower() == token.lower()
        else:
            is_match = text == token
        if not is_match:
            return None

        self.move(len(token))
        partial_match = (
            self.nameguard and self.is_name_char(self.current) and self.is_name(token)
        )
        if partial_match:
            self.goto(p)
            return None

        return token

    def _matchre_fast(self, pattern: str | re.Pattern | None):
        if not (match := self._scanre(pattern)):
            return

        self.move(len(match.group()))

    def matchre(self, pattern: str | re.Pattern) -> str | None:
        if not (match := self._scanre(pattern)):
            return None

        matched = match.group()
        token = str_from_match(match)
        self.move(len(matched))
        return token

    def _scanre(self, pattern: str | re.Pattern | None) -> re.Match[Any] | None:
        cre = cached_re_compile(pattern)
        if cre is None:
            return None
        else:
            return cre.match(self.text, self.pos)

    @property
    def linecount(self) -> int:
        return self._linecount

    def lineinfo(self, pos: int | None = None) -> LineInfo:
        if pos is None:
            pos = self._pos
        if not self._line_cache or not self._line_index:
            return LineInfo(
                filename=self.filename,
                line=0,
                col=0,
                start=0,
                end=len(self.text),
                text=self.text,
                )

        # -2 to skip over sentinel
        pos = min(pos, len(self._line_cache) - 2)
        start, line, length = self._line_cache[pos]
        end = start + length
        col = pos - start

        text = self.text[start:end]

        # only required to support includes
        n = min(len(self._line_index) - 1, line)
        filename, line = self._line_index[n]

        return LineInfo(filename, line, col, start, end, text)

    def lookahead_pos(self) -> str:
        if self.atend():
            return ''
        info = self.lineinfo()
        return '@%d:%d' % (info.line + 1, info.col + 1)

    def lookahead(self) -> str:
        if self.atend():
            return ''
        info = self.lineinfo()
        text = info.text[info.col : info.col + 1 + 80]
        return self.split_block_lines(text)[0].rstrip()

    def get_line(self, n: int | None = None) -> str:
        if n is None:
            n = self.line
        return self._lines[n]

    def get_lines(self, start: int | None = None, end: int | None = None) -> list[str]:
        if start is None:
            start = 0
        if end is None:
            end = len(self._lines)
        return self._lines[start : end + 1]

    def line_index(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        if end is None:
            end = len(self._line_index)
        return self._line_index[start : 1 + end]

    def line_index_at(self, start: int = 0, end: int | None = None) -> list[LineIndexInfo]:
        return self.line_index(start, end)

    def eat_whitespace_at(self, c: Cursor) -> None:
        self.eat_whitespace()

    def eat_comments_at(self, c: Cursor) -> None:
        self.eat_comments()

    def eat_eol_comments_at(self, c: Cursor) -> None:
        self.eat_comments()

    def next_token_at(self, c: Cursor) -> None:
        self.next_token()

    def match_at(self, token: str, c: Cursor) -> str | None:
        return self.match(token)

    def matchre_at(self, pattern: str | re.Pattern, c: Cursor) -> str | None:
        return self.matchre(pattern)

    def posline_at(self, pos: int) -> int:
        return self.posline(pos)

    def poscol_at(self, pos: int) -> int:
        return self.poscol(pos)

    def lineinfo_at(self, pos: int) -> LineInfo:
        return self.lineinfo(pos)

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def __json__(self, seen: set[int] | None = None) -> str | None:
        return None
