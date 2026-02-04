# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import warnings
from collections.abc import Collection
from dataclasses import dataclass, field
from typing import Any, override

from .tokenizing import NullTokenizer, Tokenizer
from .util import Undefined
from .util.configs import Config
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
    namechars: str | None = None
    nameguard: bool | None = None  # implied by namechars
    whitespace: str | None = Undefined  # type: ignore
    parseinfo: bool = False

    # deprecated: some old projects use these
    owner: Any = None
    extra: Any = None
    comments_re: re.Pattern | str | None = None  # WARNING: deprecated
    eol_comments_re: re.Pattern | str | None = None  # WARNING: deprecated

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase:
            self.keywords = {k.upper() for k in self.keywords}
        super().__post_init__()

        if not self.memoization:
            self.left_recursion = False

        if self.namechars:
            self.nameguard = True

        if isinstance(self.semantics, type):
            raise TypeError(
                f'semantics must be an object instance or None, not class {self.semantics!r}',
            )

        self._deprecate_and_compile_comments()

    def _deprecate_and_compile_comments(self):
        # note: handle deprecations gracefully
        if self.comments_re:
            warnings.warn(
                'ParserConfig.comments_re is deprecated: use `comments`',
                stacklevel=3,
            )
            if not self.comments:
                self.comments = str(self.comments_re)
            del self.comments_re

        if self.eol_comments_re:
            warnings.warn(
                'ParserConfig.eol_comments_re is deprecated: use `eol_comments`',
                stacklevel=3,
            )
            if not self.eol_comments:
                self.eol_comments = str(self.eol_comments_re)
            del self.eol_comments_re

        if self.comments and isinstance(self.comments, str):
            cached_re_compile(self.comments)
        if self.eol_comments and not isinstance(self.eol_comments, re.Pattern):
            cached_re_compile(self.eol_comments)
        if self.whitespace and not isinstance(self.whitespace, re.Pattern):
            cached_re_compile(self.whitespace)

    def effective_rule_name(self):
        # note: there are legacy reasons for this mess
        return self.start_rule or self.rule_name or self.start

    @override
    def override(self, **settings: Any) -> ParserConfig:
        result = super().override(**settings)
        if 'grammar' in settings:
            result.name = result.grammar
        self._deprecate_and_compile_comments()
        return result
