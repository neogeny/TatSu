# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import cache
from typing import Any

from ..config import ParserConfig
from ..exceptions import (
    FailedLeftRecursion,
    FailedParse,
    ParseException,
)
from ..input import Cursor, NullText, Text
from ..objectmodel import ModelBuilderSemantics
from ..util import (
    prune_dict,
    safe_name,
)
from ..util.boundeddict import BoundedDict
from ..util.heart import Heart
from .ast import AST
from .ctx import Ctx, Func
from .infos import MemoKey, RuleInfo, RuleResult
from .state import ParseState, ParseStateStack
from .tracing import ConsoleTracer, NullTracer, Tracer


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


class ParserCore(Ctx):
    states: ParseStateStack  # type: ignore

    def __init__(
        self,
        /,
        *,
        config: ParserConfig | None = None,
        asmodel: bool = False,
        **settings: Any,
    ) -> None:
        super().__init__()

        config = ParserConfig.new(config, **settings)
        assert isinstance(config, ParserConfig)
        assert isinstance(config, ParserConfig)
        self._config: ParserConfig = config
        self._active_config: ParserConfig = self._config

        self.input: Text = NullText()
        self.states: ParseStateStack = ParseStateStack(cursor=self.input.newcursor())
        if not self.config.semantics and asmodel:
            self.config.semantics = ModelBuilderSemantics()
        self.semantics: type | None = config.semantics
        self._furthest_exception: FailedParse | None = None

        self._initialize_caches()
        self.tracer: Tracer = NullTracer()
        self.heart: Heart | None = config.heart
        self.lastbeat_time = 0.0
        self.lastbeat_pos: int = 0
        self.update_tracer()

    def _initialize_caches(self) -> None:
        self._furthest_exception = None
        self._memos: MemoCache = BoundedDict(
            int(max(1.0, self.config.perlinememos) * self.cursor.linecount)
        )
        self._results: MemoCache = {}
        self.states = ParseStateStack(cursor=self.input.newcursor())

    def _reset(self) -> None:
        self._initialize_caches()
        self.keywords: set[str] = set(self.config.keywords or ())
        self.semantics = self.config.semantics
        if self.semantics and hasattr(self.semantics, 'set_context'):
            self.semantics.set_context(self)

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
    def pos(self) -> int:
        return self.states.state.cursor.pos

    @property
    def line(self) -> int:
        return self.cursor.line

    @property
    def state(self) -> ParseState:
        return self.states.state

    @property
    def ast(self) -> AST:
        return self.states.state.ast

    @ast.setter
    def ast(self, value: AST) -> None:
        self.states.state.ast = value

    @property
    def cst(self) -> Any:
        return self.states.state.cst

    @cst.setter
    def cst(self, value: Any) -> None:
        self.states.state.cst = value

    @property
    def callstack(self) -> list[RuleInfo]:
        return self.states.callstack

    def update_tracer(self) -> Tracer:
        if self.active_config.trace:
            tracer: Tracer = ConsoleTracer(config=self.config)
        else:
            tracer = NullTracer()
        self.tracer = tracer
        return self.tracer

    def set_furthest_exception(self, e: FailedParse) -> None:
        if not self._furthest_exception or e.pos >= self._furthest_exception.pos:
            self._furthest_exception = e

    def goto(self, pos: int) -> None:
        self.states.state.cursor.goto(pos)

    def _next(self) -> Any:
        return self.cursor.next()

    def heartbeat(self) -> None:
        if self.heart is None:
            return

        if self.pos <= self.lastbeat_pos:
            return

        now = time.perf_counter()
        if now - self.lastbeat_time < 0.128:
            return

        self.heart.beat(self.cursor.line, self.cursor.linecount)

        self.lastbeat_time = now
        self.lastbeat_pos = self.pos

    def next_token(self, ri: RuleInfo | None = None) -> None:
        if not (ri and ri.is_tokn):
            self.state.cursor.next_token()

    def _define(self, keys: list[str], addkeys: list[str] | None = None) -> None:
        # NOTE: called by generated parsers
        return self.state.define(keys, addkeys)

    def define(self, keys: list[str], addkeys: list[str] | None = None) -> None:
        # NOTE: called by generated parsers
        return self.state.define(keys, addkeys)

    def setname(self, name: str) -> None:
        # NOTE: called by generated parsers
        self.state.nameset(name)

    def addname(self, name: str) -> None:
        # NOTE: called by generated parsers
        self.state.nameadd(name)

    @contextmanager
    def statescope(self, merge: bool = True) -> Generator[None, None, None]:
        self.states.push()
        try:
            yield
            if merge:
                self.states.merge()
            else:
                self.states.pop()
        except FailedParse:
            self.states.undo()
            raise

    def cut(self) -> None:
        self.state.cutseen = True
        self.tracer.trace_cut(self)

        if not self.config.prune_memos_on_cut:
            return

        cutpos = self.pos

        def unwanted(key: MemoKey, value: RuleResult | ParseException) -> bool:
            return key.pos < cutpos and not isinstance(value, FailedLeftRecursion)

        prune_dict(self._memos, unwanted)

    _cut = cut

    def find_rule(self, name: str) -> Func:
        assert name
        raise NotImplementedError

    def find_semantic_action(self, name: str) -> Callable[..., Any] | None:
        return find_cached_semantic_action(self.semantics, name)

    def newexcept(
        self,
        msg: Any,
        excls: type[FailedParse] = FailedParse,
    ) -> FailedParse:
        return excls(self.cursor, self.callstack, msg)

    @property
    def ruleinfo(self) -> RuleInfo:
        return self.callstack[-1]

    def memokey(self) -> MemoKey:
        return MemoKey(self.pos, self.ruleinfo)

    def memo(self, key: MemoKey) -> RuleOutcome | None:
        return self._memos.get(key)

    def memoize(
        self,
        key: MemoKey,
        memo: RuleResult | ParseException,
    ) -> RuleResult | ParseException:
        if key.ruleinfo.memoizable and self.config.memoization:
            self._memos[key] = memo
        return memo
