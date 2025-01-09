from __future__ import annotations

import copy
import dataclasses
import re
from collections.abc import Callable, MutableMapping
from itertools import starmap
from typing import Any, NamedTuple

from .ast import AST
from .tokenizing import Tokenizer
from .util.misc import cached_re_compile
from .util.unicode_characters import C_DERIVE


class UndefinedStr(str):
    pass


_undefined_str = UndefinedStr('>>undefined<<')


@dataclasses.dataclass
class ParserConfig:
    owner: Any = None
    name: str | None = 'Test'
    filename: str = ''
    encoding: str = 'utf-8'

    start: str | None = None  # FIXME
    start_rule: str | None = None  # FIXME
    rule_name: str | None = None  # Backward compatibility

    comments_re: re.Pattern | str | None = None
    eol_comments_re: re.Pattern | str | None = None

    tokenizercls: type[Tokenizer] | None = None  # FIXME
    semantics: type | None = None

    comment_recovery: bool = False
    memoize_lookaheads: bool = True

    colorize: bool = False
    trace: bool = False
    trace_filename: bool = False
    trace_length: int = 72
    trace_separator: str = C_DERIVE

    # parser directives
    grammar: str | None = None
    left_recursion: bool = True

    comments: str | None = None
    eol_comments: str | None = None
    keywords: list[str] | set[str] = dataclasses.field(default_factory=list)

    ignorecase: bool | None = False
    namechars: str = ''
    nameguard: bool | None = None  # implied by namechars
    whitespace: str | None = _undefined_str

    parseinfo: bool = False

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase:
            self.keywords = [k.upper() for k in self.keywords]

        if self.comments_re or self.eol_comments_re:
            raise AttributeError(
                "Both `comments_re` and `eol_comments_re` have been removed from parser configurations. " +
                "Please use `comments` and/or `eol_comments` instead`.",
            )
        del self.comments_re
        del self.eol_comments_re

        if self.comments:
            cached_re_compile(self.comments)
        if self.eol_comments:
            cached_re_compile(self.eol_comments)
        if self.whitespace:
            cached_re_compile(self.whitespace)

    @classmethod
    def new(
        cls,
        config: ParserConfig | None = None,
        owner: Any | None = None,
        **settings: Any,
    ) -> ParserConfig:
        result = cls(owner=owner)
        if config is not None:
            result = config.replace_config(config)
        return result.replace(**settings)

    # NOTE:
    #    Using functools.cache directly makes objects of this class unhashable

    def effective_rule_name(self):
        # note: there are legacy reasons for this mess
        return self.start_rule or self.rule_name or self.start

    def _find_common(self, **settings: Any) -> MutableMapping[str, Any]:
        return {
            name: value
            for name, value in settings.items()
            if value is not None and hasattr(self, name)
        }

    def replace_config(
        self, other: ParserConfig | None = None,
    ) -> ParserConfig:
        if other is None:
            return self
        elif not isinstance(other, ParserConfig):
            raise TypeError(f'Unexpected type {type(other).__name__}')
        else:
            return self.replace(**vars(other))

    # non-init fields cannot be used as arguments in `replace`, however
    # they are values returned by `vars` and `dataclass.asdict` so they
    # must be filtered out.
    # If the `ParserConfig` dataclass drops these fields, then this filter can be removed
    def _filter_non_init_fields(self, settings: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        for field in [
            field.name for field in dataclasses.fields(self) if not field.init
        ]:
            if field in settings:
                del settings[field]
        return settings

    def replace(self, **settings: Any) -> ParserConfig:
        overrides = self._filter_non_init_fields(self._find_common(**settings))
        result = dataclasses.replace(self, **overrides)
        if 'grammar' in overrides:
            result.name = result.grammar
        return result

    def merge(self, **settings: Any) -> ParserConfig:
        overrides = self._find_common(**settings)
        overrides = {
            name: value
            for name, value in overrides.items()
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
                cache.append(pl)  # noqa: PERF401
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
        return list(
            starmap(LineIndexInfo, zip(n * [name], range(n), strict=False)),
        )


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
    alerts: list[Alert] = []  # noqa: RUF012

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


@dataclasses.dataclass(slots=True)
class ParseState:
    pos: int = 0
    ast: AST = dataclasses.field(default_factory=AST)
    cst: Any = None
    alerts: list[Alert] = dataclasses.field(default_factory=list)
