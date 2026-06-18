# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import Any, Self, override

from .input import NullText
from .input.cursor import Text
from .util.configs import Config
from .util.heart import Heart
from .util.regextools import cached_re_compile
from .util.undefined import Undefined, UndefinedType
from .util.unicode_characters import C_DERIVE


DEFAULT_PERLINEMEMOS = 8


@dataclass
class ParserConfig(Config):
    name: str | None = 'Test'
    source: str = ''

    start: str | None = None

    semantics: Any = None

    comment_recovery: bool = False

    memoization: bool = True
    perlinememos: float = DEFAULT_PERLINEMEMOS
    memoize_lookaheads: bool | None = None
    prune_memos_on_cut: bool = True

    colorize: bool = True
    trace: bool = False
    trace_filename: str = ''
    trace_length: int = 72
    trace_separator: str = C_DERIVE

    # parser directives
    grammar: str | None = None
    left_recursion: bool = True

    comments: str | None = None
    eol_comments: str | None = None
    keywords: tuple[str, ...] | None = None

    ignorecase: bool | None = None
    namechars: str | None = None
    nameguard: bool | None = None  # implied by namechars
    whitespace: str | UndefinedType | None = Undefined
    parseinfo: bool = False
    heart: Heart | None = None
    heart_wait: float = 0.090

    # WARNING: DEPRECATED: some old projects use these
    owner: Any = None
    extra: Any = None
    start_rule: str | None = None
    rule_name: str | None = None
    comments_re: re.Pattern | str | None = None
    eol_comments_re: re.Pattern | str | None = None
    tokenizercls: type[Text] = NullText
    filename: str | None = None
    memo_cache_size: int | None = None

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase and self.keywords:
            self.keywords = tuple({k.upper() for k in self.keywords})
        super().__post_init__()

        if not self.memoization:
            self.left_recursion = False

        if self.namechars:
            self.nameguard = True

        if isinstance(self.semantics, type):
            raise TypeError(
                f'semantics must be an object instance or None, not class {self.semantics!r}',
            )

        self._check_deprecations()
        self._compile_comments()

    def _check_deprecations(self):
        if self.comments_re:
            warnings.warn(
                'ParserConfig.comments_re is deprecated: use `comments`',
                DeprecationWarning,
                stacklevel=3,
            )
            if not self.comments:
                self.comments = str(self.comments_re)
            del self.comments_re

        if self.eol_comments_re:
            warnings.warn(
                'ParserConfig.eol_comments_re is deprecated: use `eol_comments`',
                DeprecationWarning,
                stacklevel=3,
            )
            if not self.eol_comments:
                self.eol_comments = str(self.eol_comments_re)
            del self.eol_comments_re

        if self.memoize_lookaheads is not None:
            warnings.warn(
                'ParserConfig.memoize_lookaheads is deprecated and has no effect',
                DeprecationWarning,
                stacklevel=3,
            )
            del self.memoize_lookaheads

        if self.memo_cache_size is not None:
            warnings.warn(
                'ParserConfig.memo_cache_size is deprecated and has no effect',
                DeprecationWarning,
                stacklevel=3,
            )
            del self.memo_cache_size

        if not issubclass(self.tokenizercls, NullText):
            warnings.warn(
                'ParserConfig.tokenizercls is deprecated and has no effect',
                DeprecationWarning,
                stacklevel=3,
            )
            del self.tokenizercls

        if self.filename is not None:
            self.source = self.filename
            warnings.warn(
                'ParserConfig.filename is deprecated. Use .source instead',
                DeprecationWarning,
                stacklevel=3,
            )
            del self.filename

    def _compile_comments(self):
        if self.comments and isinstance(self.comments, str):
            cached_re_compile(self.comments)
        if self.eol_comments and not isinstance(self.eol_comments, re.Pattern):
            cached_re_compile(self.eol_comments)
        if self.whitespace and not isinstance(self.whitespace, re.Pattern):
            cached_re_compile(self.whitespace)

        for name in ('start_rule', 'rule_name'):
            if (value := getattr(self, name, None)) is None:
                continue
            warnings.warn(
                message=(
                    f'\nSetting {name}={value!r} is deprecated.'
                    f' Use start={value!r} for the name of the start rule.'
                ),
                category=DeprecationWarning,
                stacklevel=2,
            )
            break
        self.start = self.effective_start_rule_name()

    def effective_start_rule_name(self):
        # NOTE: there are legacy reasons for this mess
        return (
            self.start
            or getattr(self, 'start_rule', None)
            or getattr(self, 'rule_name', None)
        )

    @override
    def override(self, /, hard: bool = False, **settings: Any) -> Self:
        result = super().override(hard=hard, **settings)
        assert isinstance(result, ParserConfig)
        if 'grammar' in settings:
            result.name = result.grammar
        self._check_deprecations()
        self._compile_comments()
        return result
