"""
The Buffer class provides the functionality required by a parser-driven lexer.

Line analysis and caching are done so the parser can freely move with goto(p)
to any position in the parsed text, and still recover accurate information
about source lines and content.
"""
from __future__ import annotations

import re
from itertools import repeat, takewhile
from pathlib import Path
from typing import Any

from .exceptions import ParseError
from .infos import (
    CommentInfo,
    LineIndexInfo,
    LineInfo,
    ParserConfig,
    PosLine,
    UndefinedStr,
)
from .tokenizing import Tokenizer
from .util import (
    contains_sublist,
    extend_list,
    identity,
)
from .util.misc import cached_re_compile, match_to_find

DEFAULT_WHITESPACE_RE = re.compile(r'(?m)\s+')

# for backwards compatibility with existing parsers
LineIndexEntry = LineIndexInfo


class Buffer(Tokenizer):

    def __init__(
        self, text, /, config: ParserConfig | None = None, **settings: Any,
    ):
        super().__init__()
        config = ParserConfig.new(config=config, owner=self, **settings)
        self.config = config

        text = str(text)
        self.text = self.original_text = text

        self.whitespace_re = self.build_whitespace_re(config.whitespace)
        self.nameguard = (
            config.nameguard
            if config.nameguard is not None
            else bool(self.whitespace_re) or bool(config.namechars)
        )
        self._namechar_set = set(config.namechars)

        self._pos = 0
        self._len = 0
        self._linecount = 0
        self._lines: list[str] = []
        self._line_index: list[LineIndexInfo] = []
        self._line_cache: list[PosLine] = []
        self._comment_index: list[CommentInfo] = []

        self._preprocess()
        self._postprocess()

    @property
    def filename(self):
        return self.config.filename

    @property
    def ignorecase(self):
        return self.config.ignorecase

    @property
    def whitespace(self):
        return self.config.whitespace

    @staticmethod
    def build_whitespace_re(whitespace):
        if type(whitespace) is UndefinedStr:
            return DEFAULT_WHITESPACE_RE
        if whitespace in {None, ''}:
            return None
        elif isinstance(whitespace, re.Pattern):
            return whitespace
        elif whitespace:
            return cached_re_compile(whitespace)
        else:
            return None

    def _preprocess(self, *args, **kwargs):
        lines, index = self._preprocess_block(self.filename, self.text)
        self._lines = lines
        self._line_index = index
        self.text = self.join_block_lines(lines)

    def _postprocess(self):
        cache, count = PosLine.build_line_cache(self._lines)
        self._line_cache = cache
        self._linecount = count
        self._len = len(self.text)

    def _preprocess_block(self, name, block, **kwargs):
        lines = self.split_block_lines(block)
        index = LineIndexInfo.block_index(name, len(lines))
        return self.process_block(name, lines, index, **kwargs)

    def split_block_lines(self, block):
        return block.splitlines(True)

    def join_block_lines(self, lines):
        return ''.join(lines)

    def process_block(self, name, lines, index, **kwargs):
        return lines, index

    def include(self, lines, index, i, j, name, block, **kwargs):
        blines, bindex = self._preprocess_block(name, block, **kwargs)
        assert len(blines) == len(bindex)
        lines[i:j] = blines
        index[i:j] = bindex
        assert len(lines) == len(index)
        return j + len(blines) - 1

    def include_file(self, source, name, lines, index, i, j):
        text, filename = self.get_include(source, name)
        return self.include(lines, index, i, j, filename, text)

    def get_include(self, source, filename):
        source = Path(source).resolve()
        base = source.parent
        include = base / filename
        try:
            with include.open() as f:
                return f.read(), include
        except OSError as e:
            raise ParseError(f'include not found: {include}') from e

    def replace_lines(self, i, j, name, block):
        lines = self.split_block_lines(self.text)
        index = list(self._line_index)

        endline = self.include(lines, index, i, j, name, block)

        self.text = self.join_block_lines(lines)
        self._line_index = index
        self._postprocess()

        newtext = self.join_block_lines(lines[j + 1: endline + 2])
        return endline, newtext

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, p):
        self.goto(p)

    @property
    def line(self):
        return self.posline()

    @property
    def col(self):
        return self.poscol()

    def posline(self, pos=None):
        if pos is None:
            pos = self._pos
        return self._line_cache[pos].line

    def poscol(self, pos=None):
        if pos is None:
            pos = self._pos
        start = self._line_cache[pos].start
        return pos - start

    def atend(self):
        return self._pos >= self._len

    def ateol(self):
        return self.atend() or self.current in '\r\n'

    @property
    def current(self):
        if self._pos >= self._len:
            return None
        return self.text[self._pos]

    def at(self, p):
        if p >= self._len:
            return None
        return self.text[p]

    def peek(self, n=1):
        return self.at(self._pos + n)

    def next(self):
        if self.atend():
            return None
        c = self.text[self._pos]
        self._pos += 1
        return c

    def goto(self, pos):
        self._pos = max(0, min(len(self.text), pos))

    def move(self, n):
        self.goto(self.pos + n)

    def comments(self, p, clear=False):
        if not self.config.comment_recovery or not self._comment_index:
            return CommentInfo([], [])

        n = self.posline(p)
        if n >= len(self._comment_index):
            return CommentInfo([], [])

        eolcmm = []
        if n < len(self._comment_index):
            eolcmm = self._comment_index[n].eol
            if clear:
                self._comment_index[n].eol = []

        cmm = []
        while n >= 0 and self._comment_index[n].inline:
            cmm.insert(0, self._comment_index[n].inline)
            if clear:
                self._comment_index[n].inline = []
            n -= 1

        return CommentInfo(cmm, eolcmm)

    def _index_comments(self, comments, selector):
        if comments and self.config.comment_recovery:
            n = self.line
            extend_list(
                self._comment_index, n, default=CommentInfo.new_comment,
            )
            previous = selector(self._comment_index[n])
            if not contains_sublist(
                previous, comments,
            ):  # FIXME: will discard repeated comments
                previous.extend(comments)

    def _eat_regex(self, regex):
        if not regex:
            return
        while self._matchre_fast(regex):
            pass

    def _eat_regex_list(self, regex):
        if not regex:
            return []
        regex = cached_re_compile(regex)
        return list(takewhile(identity, map(self.matchre, repeat(regex))))

    def eat_whitespace(self):
        return self._eat_regex(self.whitespace_re)

    def eat_comments(self):
        comments = self._eat_regex_list(self.config.comments)
        self._index_comments(comments, lambda x: x.inline)

    def eat_eol_comments(self):
        comments = self._eat_regex_list(self.config.eol_comments)
        self._index_comments(comments, lambda x: x.eol)

    def next_token(self):
        p = None
        while self._pos != p:
            p = self._pos
            self.eat_eol_comments()
            self.eat_comments()
            self.eat_whitespace()

    def skip_to(self, c):
        p = self._pos
        le = self._len
        while p < le and self.text[p] != c:
            p += 1
        self.goto(p)
        return self.pos

    def skip_past(self, c):
        self.skip_to(c)
        self.next()
        return self.pos

    def skip_to_eol(self):
        return self.skip_to('\n')

    def scan_space(self):
        return (
            self.whitespace_re and self._scanre(self.whitespace_re) is not None
        )

    def is_space(self):
        return self.scan_space()

    def is_name_char(self, c):
        return c is not None and (c.isalnum() or c in self._namechar_set)

    def match(self, token: str) -> str | None:
        if token is None:
            return self.atend()

        p = self.pos
        if self.ignorecase:
            is_match = self.text[p: p + len(token)].lower() == token.lower()
        else:
            is_match = self.text[p: p + len(token)] == token

        if not is_match:
            return None

        self.move(len(token))
        partial_match = (
            self.nameguard
            and token
            and token[0].isalpha()
            and self.is_name_char(self.current)
            and all(self.is_name_char(t) for t in token)
        )
        if partial_match:
            self.goto(p)
            return None

        return token

    def _matchre_fast(self, pattern):
        if not (match := self._scanre(pattern)):
            return

        self.move(len(match.group()))

    def matchre(self, pattern):
        if not (match := self._scanre(pattern)):
            return None

        matched = match.group()
        token = match_to_find(match)
        self.move(len(matched))
        return token

    def _scanre(self, pattern):
        cre = cached_re_compile(pattern)
        return cre.match(self.text, self.pos)

    @property
    def linecount(self):
        return self._linecount

    def line_info(self, pos=None):
        if pos is None:
            pos = self._pos

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

    def lookahead_pos(self):
        if self.atend():
            return ''
        info = self.line_info()
        return '~%d:%d' % (info.line + 1, info.col + 1)

    def lookahead(self):
        if self.atend():
            return ''
        info = self.line_info()
        text = info.text[info.col: info.col + 1 + 80]
        text = self.split_block_lines(text)[0].rstrip()
        return f'{text}'

    def get_line(self, n=None):
        if n is None:
            n = self.line
        return self._lines[n]

    def get_lines(self, start=None, end=None):
        if start is None:
            start = 0
        if end is None:
            end = len(self._lines)
        return self._lines[start: end + 1]

    def line_index(self, start=0, end=None):
        if end is None:
            end = len(self._line_index)
        return self._line_index[start: 1 + end]

    def __repr__(self):
        return '%s@%d' % (type(self).__name__, self.pos)

    def __json__(self, seen=None):
        return None
