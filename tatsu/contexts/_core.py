# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from functools import cache
from typing import Any

from ..collections import BoundedDict
from ..exceptions import (
    FailedLeftRecursion,
    FailedParse,
    ParseException,
)
from ..infos import ParserConfig
from ..tokenizing import Cursor, NullTokenizer, Tokenizer
from ..tokenizing.textlines import TextLinesTokenizer
from ..util import (
    prune_dict,
    safe_name,
)
from .ast import AST
from .infos import MemoKey, RuleInfo, RuleResult
from .state import ParseState, ParseStateStack
from .tracing import EventTracer, InfoEventTracer, NullEventTracer


type RuleOutcome = RuleResult | ParseException
type MemoCache = dict[MemoKey, RuleOutcome]


@cache
def find_cached_semantic_action(semantics: Any, name: str) -> Callable[..., Any] | None:
    if not semantics:
        return None

    for rulename in (name, safe_name(name), name.strip('_'), f'_{name}', f'_{name}_'):
        action = getattr(semantics, safe_name(rulename), None)
        if callable(action):
            break
    else:
        action = None

    if not callable(action):
        action = getattr(semantics, '_default', None)

    if not callable(action):
        action = None

    return action


class ParserCore:
    def __init__(
        self,
        /,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
    ) -> None:
        super().__init__()

        config = ParserConfig.new(config, **settings)
        assert isinstance(config, ParserConfig)
        tokcls = config.tokenizercls
        if tokcls is None or isinstance(tokcls, NullTokenizer):
            config = config.override(tokenizercls=TextLinesTokenizer)
        assert isinstance(config, ParserConfig)
        self._config: ParserConfig = config
        self._active_config: ParserConfig = self._config

        self.tokenizer: Tokenizer = NullTokenizer()
        self._states: ParseStateStack = ParseStateStack(
            cursor=self.tokenizer.newcursor()
        )
        self.semantics: type | None = config.semantics
        self._furthest_exception: FailedParse | None = None

        self._initialize_caches()
        self.tracer: EventTracer = NullEventTracer()
        self.update_tracer()

    def _initialize_caches(self) -> None:
        self._furthest_exception = None
        self._memos: MemoCache = BoundedDict(self.config.memo_cache_size)
        self._results: MemoCache = {}
        self._states = ParseStateStack(cursor=self.tokenizer.newcursor())

    def _reset(self, config: ParserConfig) -> ParserConfig:
        self._initialize_caches()
        self.keywords: set[str] = set(config.keywords)
        self.semantics = config.semantics
        if self.semantics and hasattr(self.semantics, 'set_context'):
            self.semantics.set_context(self)
        return config

    @property
    def config(self):
        return self._active_config

    @property
    def active_config(self) -> ParserConfig:
        return self._active_config

    @property
    def self_config(self) -> ParserConfig:
        return self._config

    @property
    def cursor(self) -> Cursor:
        return self.state.cursor

    @property
    def tokenizercls(self) -> type[Tokenizer]:
        if self.config.tokenizercls is None:
            return TextLinesTokenizer
        return self.config.tokenizercls

    @property
    def last_node(self) -> Any:
        return self.states.last_node

    @last_node.setter
    def last_node(self, value: Any) -> None:
        self.states.last_node = value

    @property
    def pos(self) -> int:
        return self.cursor.pos

    @property
    def line(self) -> int:
        return self.cursor.line

    @property
    def states(self) -> ParseStateStack:
        return self._states

    @property
    def state(self) -> ParseState:
        return self.states.top

    @property
    def ast(self) -> AST:
        return self.state.ast

    @ast.setter
    def ast(self, value: AST) -> None:
        self.state.ast = value

    @property
    def cst(self) -> Any:
        return self.state.cst

    @cst.setter
    def cst(self, value: Any) -> None:
        self.state.cst = value

    @property
    def ruleinfo_stack(self) -> list[RuleInfo]:
        return self.states.ruleinfo_stack

    @property
    def lookahead(self) -> int:
        return self.states.lookahead

    @lookahead.setter
    def lookahead(self, value: Any) -> None:
        self.states.lookahead = value

    def update_tracer(self) -> EventTracer:
        if self.active_config.trace:
            tracer: EventTracer = InfoEventTracer(
                self.ruleinfo_stack, config=self.config
            )
        else:
            tracer = NullEventTracer()
        self.tracer = tracer
        return self.tracer

    def set_furthest_exception(self, e: FailedParse) -> None:
        if not self._furthest_exception or e.pos > self._furthest_exception.pos:
            self._furthest_exception = e

    def goto(self, pos: int) -> None:
        self.cursor.goto(pos)

    def _next(self) -> Any:
        return self.cursor.next()

    def next_token(self, ri: RuleInfo | None = None) -> None:
        if not (ri and ri.is_token_rule()):
            self.cursor.next_token()

    def _define(self, keys: list[str], addkeys: list[str] | None = None) -> None:
        # NOTE: called by generated parsers
        return self.states.define(keys, addkeys)

    def define(self, keys: list[str], addkeys: list[str] | None = None) -> None:
        # NOTE: called by generated parsers
        return self.states.define(keys, addkeys)

    def setname(self, name: str) -> None:
        # NOTE: called by generated parsers
        self.states.setname(name)

    def addname(self, name: str) -> None:
        # NOTE: called by generated parsers
        self.states.addname(name)

    def pushstate(self, ast: Any = None) -> None:
        self.states.push(ast=ast)

    def popstate(self) -> ParseState:
        return self.states.pop(self.pos)

    def mergestate(self) -> ParseState:
        return self.states.merge()

    def undostate(self) -> None:
        self.states.pop()

    def cut(self) -> None:
        self.states.set_cut_seen()
        self.tracer.trace_cut(self.cursor)

        def prune(cache: dict[Any, Any], cut_pos: int) -> None:
            prune_dict(
                cache,
                lambda k, v: k[0] < cut_pos and not isinstance(v, FailedLeftRecursion),
            )

        if self.config.prune_memos_on_cut:
            prune(self._memos, self.pos)

    _cut = cut

    def memoization(self) -> bool:
        if not self.config.memoization:
            return False
        return self.config.memoize_lookaheads or self.lookahead == 0

    def find_rule(self, name: str) -> Callable[..., Any]:
        assert name
        raise NotImplementedError

    def find_semantic_action(self, name: str) -> Callable[..., Any] | None:
        return find_cached_semantic_action(self.semantics, name)

    def newexcept(
        self,
        msg: Any,
        excls: type[FailedParse] = FailedParse,
    ) -> FailedParse:
        if issubclass(excls, FailedLeftRecursion):
            rulestack: list[str] = []
        else:
            rulestack = [r.name for r in reversed(self.ruleinfo_stack)]
        return excls(self.cursor.lineinfo(), rulestack, msg)

    @property
    def ruleinfo(self) -> RuleInfo:
        return self.ruleinfo_stack[-1]

    def memokey(self) -> MemoKey:
        return MemoKey(self.pos, self.ruleinfo)

    def memoize(
        self,
        key: MemoKey,
        memo: RuleResult | ParseException,
    ) -> RuleResult | ParseException:
        if self.memoization() and key.ruleinfo.is_memo:
            self._memos[key] = memo
        return memo
