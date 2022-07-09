from __future__ import annotations

import copy
import dataclasses
from typing import (
    Any,
    Callable,
    Mapping,
    NamedTuple,
    Type,
)

from .ast import AST
from .util.unicode_characters import C_DERIVE
from .tokenizing import Tokenizer


COMMENTS_RE = r'\(\*((?:.|\n)*?)\*\)'
EOL_COMMENTS_RE = r'#([^\n]*?)$'


@dataclasses.dataclass
class ParserConfig:
    owner: Any = None
    name: str|None = 'Test'
    filename: str = ''
    encoding: str = 'utf-8'

    start: str|None = None  # FIXME
    start_rule: str|None = None  # FIXME
    rule_name: str|None = None  # Backward compatibility

    comments_re: str|None = COMMENTS_RE
    eol_comments_re: str|None = EOL_COMMENTS_RE

    tokenizercls: Type[Tokenizer]|None = None  # FIXME
    semantics: Type|None = None

    comment_recovery: bool = False
    memoize_lookaheads: bool = True

    colorize: bool = False
    trace: bool = False
    trace_filename: bool = False
    trace_length: int = 72
    trace_separator: str = C_DERIVE

    # parser directives
    grammar: str|None = None
    left_recursion: bool = True

    comments: str|None = None
    eol_comments: str|None = None
    keywords: list[str]|set[str] = dataclasses.field(default_factory=list)  # type: ignore

    ignorecase: bool|None = False
    namechars: str = ''
    nameguard: bool|None = None  # implied by namechars
    whitespace: str|None = None

    parseinfo: bool = False

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase:
            self.keywords = [k.upper() for k in self.keywords]
        if self.comments:
            self.comments_re = self.comments
        if self.eol_comments:
            self.eol_comments_re = self.eol_comments

    @classmethod
    def new(cls, config: ParserConfig|None = None, owner: Any|None = None, **settings: Any) -> ParserConfig:
        result = cls(owner=owner)
        if config is not None:
            result = config.replace_config(config)
        return result.replace(**settings)

    def effective_rule_name(self):
        # note: there are legacy reasons for this mess
        return (
            self.start_rule or
            self.rule_name or
            self.start
        )

    def _find_common(self, **settings: Any) -> Mapping[str, Any]:
        return {
            name: value
            for name, value in settings.items()
            if value is not None and hasattr(self, name)
        }

    def replace_config(self, other: ParserConfig|None = None) -> ParserConfig:
        if other is None:
            return self
        elif not isinstance(other, ParserConfig):
            raise TypeError(f'Unexpected type {type(other).__name__}')
        else:
            return self.replace(**vars(other))

    def replace(self, **settings: Any) -> ParserConfig:
        overrides = self._find_common(**settings)
        result = dataclasses.replace(self, **overrides)
        if 'grammar' in overrides:
            result.name = result.grammar
        return result

    def merge(self, **settings: Any) -> ParserConfig:
        overrides = self._find_common(**settings)
        overrides = {
            name: value for name, value in overrides.items()
            if getattr(self, name, None) is None
        }
        return self.replace(**overrides)

    def asdict(self):
        # warning: it seems dataclasses.asdict does a deepcopy
        # result = dataclasses.asdict(self)
        result = copy.copy(vars(self))
        result.pop('owner', None)
        return result


class PosLine(NamedTuple):
    start: int
    line: int
    length: int

    @staticmethod
    def build_line_cache(lines):
        cache = []
        n = 0
        i = 0
        for n, line in enumerate(lines):
            pl = PosLine(i, n, len(line))
            for _ in line:
                cache.append(pl)
            i += len(line)
        n += 1
        if lines and lines[-1] and lines[-1][-1] in '\r\n':
            n += 1
        cache.append(PosLine(i, n, 0))
        return cache, n


class LineIndexInfo(NamedTuple):
    filename: str
    line: int

    @staticmethod
    def block_index(name, n):
        return list(LineIndexInfo(line, i) for line, i in zip(n * [name], range(n)))


class LineInfo(NamedTuple):
    filename: str
    line: int
    col: int
    start: int
    end: int
    text: int


class CommentInfo(NamedTuple):
    inline: list
    eol: list

    @staticmethod
    def new_comment():
        return CommentInfo([], [])


class Alert(NamedTuple):
    level: int = 1
    message: str = ''


class ParseInfo(NamedTuple):
    tokenizer: Any
    rule: str
    pos: int
    endpos: int
    line: int
    endline: int
    alerts: list[Alert] = []

    def text_lines(self):
        return self.tokenizer.get_lines(self.line, self.endline)

    def line_index(self):
        return self.tokenizer.line_index(self.line, self.endline)

    @property
    def buffer(self):
        return self.tokenizer


class MemoKey(NamedTuple):
    pos: int
    rule: str
    state: Any


class RuleInfo(NamedTuple):
    name: str
    impl: Callable
    is_leftrec: bool
    is_memoizable: bool
    is_name: bool
    params: list
    kwparams: dict

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, RuleInfo):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class RuleResult(NamedTuple):
    node: Any
    newpos: int
    newstate: Any


@dataclasses.dataclass
class ParseState:
    pos: int = 0
    ast: AST = dataclasses.field(default_factory=AST)
    cst: Any = None
    alerts: list[Alert] = dataclasses.field(default_factory=list)
