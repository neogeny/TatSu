from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass, field
from typing import Any, override

from .tokenizing import NullTokenizer, Tokenizer
from .util import Undefined
from .util.configurations import Config
from .util.misc import cached_re_compile
from .util.unicode_characters import C_DERIVE

MEMO_CACHE_SIZE = 4 * 1024


@dataclass
class ParserConfig(Config):
    name: str | None = 'Test'
    filename: str = ''
    encoding: str = 'utf-8'

    start: str | None = None  # FIXME
    start_rule: str | None = None  # FIXME
    rule_name: str | None = None  # Backward compatibility

    comments_re: re.Pattern | str | None = None  # WARNING: deprecated
    eol_comments_re: re.Pattern | str | None = None  # WARNING: deprecated

    tokenizercls: type[Tokenizer] = NullTokenizer
    semantics: Any = None

    comment_recovery: bool = False

    memoization: bool = True
    memoize_lookaheads: bool = True
    memo_cache_size: int = MEMO_CACHE_SIZE
    prune_memos_on_cut: bool = True

    colorize: bool = True  # INFO: requires the colorama library
    trace: bool = False
    trace_filename: str = ''
    trace_length: int = 72
    trace_separator: str = C_DERIVE

    # parser directives
    grammar: str | None = None
    left_recursion: bool = True

    comments: str | None = None
    eol_comments: str | None = None
    keywords: Collection[str] = field(default_factory=set)

    ignorecase: bool = False
    namechars: str = ''
    nameguard: bool | None = None  # implied by namechars
    whitespace: str | None = None
    whitespace: str | None = Undefined  # type: ignore
    parseinfo: bool = False

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase:
            self.keywords = {k.upper() for k in self.keywords}
        super().__post_init__()
        if self.comments_re or self.eol_comments_re:
            raise AttributeError(
                "Both `comments_re` and `eol_comments_re` "
                "have been removed from parser configuration. "
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

        if not self.memoization:
            self.left_recursion = False

        if self.namechars:
            self.nameguard = True

        if isinstance(self.semantics, type):
            raise TypeError(
                f'semantics must be an object instance or None, not class {semantics!r}',
            )

    def effective_rule_name(self):
        # note: there are legacy reasons for this mess
        return self.start_rule or self.rule_name or self.start

    @override
    def replace(self, **settings: Any) -> ParserConfig:
        result = super().replace(**settings)
        if 'grammar' in settings:
            result.name = result.grammar
        return result
