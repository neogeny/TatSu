from __future__ import annotations

from collections import namedtuple
import dataclasses
from pathlib import Path
from typing import (
    Any,
    Mapping,
    Optional,
    Set,
    Type,
)

from .ast import AST
from .util.unicode_characters import C_DERIVE


@dataclasses.dataclass(frozen=False)
class ParserConfig:
    owner: object = None
    filename: str = ''
    encoding: str = 'utf-8'

    start_rule: Optional[str] = None  # FIXME
    # directives: Mapping[str, Any]  = dataclasses.field(default_factory=dict)

    # tokenizercls: Optional[Type] = None
    semantics: Optional[Type] = None

    namechars: str = ''
    nameguard: Optional[bool] = None  # implied by namechars
    whitespace: Optional[str] = None

    comments_re: Optional[str] = None
    eol_comments_re: Optional[str] = None
    comment_recovery: bool = False

    ignorecase: bool = False
    keywords: list[str] = dataclasses.field(default_factory=list)
    left_recursion: bool = True
    memoize_lookaheads: bool = True
    parseinfo: bool = False

    colorize: bool = False

    trace: bool = False
    trace_filename: bool = False
    trace_length: int = 72
    trace_separator: str = C_DERIVE

    def __post_init__(self):  # noqa
        if self.ignorecase and self.keywords:
            self.keywords = {k.upper() for k in self.keywords}

    @classmethod
    def new(cls, other, /, **settings) -> ParserConfig:
        config = ParserConfig()
        config = config.merge_config(other)
        config = config.merge(**settings)
        return config

    def merge_config(self, other: ParserConfig) -> ParserConfig:
        if other is None:
            return self
        else:
            return self.merge(**vars(other))

    def merge(self, **settings: Mapping[str, Any]) -> ParserConfig:
        overrides = {
            name: value
            for name, value in settings.items()
            if value is not None and hasattr(self, name) and name != 'owner'
        }
        return dataclasses.replace(self, **overrides)

    def asdict(self):
        return dataclasses.asdict(self)


class PosLine(namedtuple('_PosLine', ['start', 'line', 'length'])):
    __slots__ = ()

    @staticmethod
    def build_line_cache(lines):
        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for c in line:
                cache.append(pl)
            i += len(line)
        n += 1
        if lines and lines[-1] and lines[-1][-1] in '\r\n':
            n += 1
        cache.append(PosLine(i, n, 0))
        return cache, n


class LineIndexInfo(namedtuple('_LineIndexInfoBase', ['filename', 'line'])):
    __slots__ = ()

    @staticmethod
    def block_index(name, n):
        return list(LineIndexInfo(line, i) for line, i in zip(n * [name], range(n)))


class LineInfo(namedtuple('_LineInfo', ['filename', 'line', 'col', 'start', 'end', 'text'])):
    __slots__ = ()


class CommentInfo(namedtuple('_CommentInfo', ['inline', 'eol'])):
    __slots__ = ()

    @staticmethod
    def new_comment():
        return CommentInfo([], [])


_ParseInfo = namedtuple(
    '_ParseInfo',
    [
        'tokenizer',
        'rule',
        'pos',
        'endpos',
        'line',
        'endline',
    ]
)


class ParseInfo(_ParseInfo):
    __slots__ = ()

    def text_lines(self):
        return self.tokenizer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.tokenizer.line_index(self.line, self.endline)


MemoKey = namedtuple(
    'MemoKey',
    [
        'pos',
        'rule',
        'state'
    ]
)


_RuleInfo = namedtuple(
    '_RuleInfo',
    [
        'name',
        'impl',
        'is_leftrec',
        'is_memoizable',
        'is_name',
        'params',
        'kwparams',
    ]
)


class RuleInfo(_RuleInfo):
    __slots__ = ()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


RuleResult = namedtuple(
    'RuleResult',
    [
        'node',
        'newpos',
        'newstate',
    ]
)


@dataclasses.dataclass
class ParseState(object):
    pos: int = 0
    ast: AST = dataclasses.field(default_factory=AST)
    cst: Any = None
