from __future__ import annotations

import copy
import dataclasses
import re
from collections.abc import Collection, MutableMapping
from dataclasses import dataclass, field
from typing import Any

from .infos import _undefined_str
from .tokenizing import Tokenizer
from .util.misc import cached_re_compile
from .util.unicode_characters import C_DERIVE

MEMO_CACHE_SIZE = 1024


@dataclass
class ParserConfig:
    name: str | None = 'Test'
    filename: str = ''
    encoding: str = 'utf-8'

    start: str | None = None  # FIXME
    start_rule: str | None = None  # FIXME
    rule_name: str | None = None  # Backward compatibility

    comments_re: re.Pattern | str | None = None  # WARNING: deprecated
    eol_comments_re: re.Pattern | str | None = None  # WARNING: deprecated

    tokenizercls: type[Tokenizer] | None = None  # FIXME
    semantics: type | None = None

    comment_recovery: bool = False

    memoization: bool = True
    memoize_lookaheads: bool = True
    memo_cache_size: int = MEMO_CACHE_SIZE

    colorize: bool = True  # INFO: requires the colorama library
    trace: bool = False
    trace_filename: bool = False
    trace_length: int = 72
    trace_separator: str = C_DERIVE

    # parser directives
    grammar: str | None = None
    left_recursion: bool = True

    comments: str | None = None
    eol_comments: str | None = None
    keywords: Collection[str] = field(default_factory=set)

    ignorecase: bool | None = False
    namechars: str = ''
    nameguard: bool | None = None  # implied by namechars
    whitespace: str | None = _undefined_str

    parseinfo: bool = False

    def __post_init__(self):  # pylint: disable=W0235
        if self.ignorecase:
            self.keywords = {k.upper() for k in self.keywords}

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

    @classmethod
    def new(
        cls,
        config: ParserConfig | None = None,
        **settings: Any,
    ) -> ParserConfig:
        result = cls()
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
        for dcfield in [
            f.name for f in dataclasses.fields(self) if not f.init
        ]:
            if dcfield in settings:
                del settings[dcfield]
        return settings

    def replace(self, **settings: Any) -> ParserConfig:
        if settings.get('whitespace') is _undefined_str:
            del settings['whitespace']
        settings = dict(self._filter_non_init_fields(settings))
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
        return copy.copy(vars(self))
