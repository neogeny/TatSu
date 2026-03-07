# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast as stdlib_ast
import inspect
from collections.abc import Callable
from contextlib import suppress
from functools import cache
from typing import Any

from ..ast import AST
from ..collections import BoundedDict
from ..exceptions import (
    FailedLeftRecursion,
    FailedParse,
    FailedSemantics,
    KeywordError,
    ParseError,
    ParseException,
)
from ..infos import ParseInfo, ParserConfig
from ..tokenizing import Cursor, NullCursor, NullTokenizer, Tokenizer
from ..tokenizing.textlines import TextLinesTokenizer
from ..util import (
    Undefined,
    boundcall,
    deprecated,
    is_eval_safe,
    is_list,
    prune_dict,
    safe_builtins,
    safe_eval,
    safe_name,
    trim,
)
from .infos import MemoKey, RuleInfo, RuleResult, closure
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


class Engine:
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

        self._initialize_caches()
        self.tracer: EventTracer = NullEventTracer()
        self.update_tracer()

    def _initialize_caches(self) -> None:
        self._furthest_exception: FailedParse | None = None
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

    def _set_furthest_exception(self, e: FailedParse) -> None:
        if not self._furthest_exception or e.pos > self._furthest_exception.pos:
            self._furthest_exception = e

    def parse(
        self,
        text: Any,
        /,
        *,
        config: ParserConfig | None = None,
        **settings: Any,
    ) -> Any:
        config = self.config.override_config(config)
        assert isinstance(config, ParserConfig)
        config = config.override(**settings)
        assert isinstance(config, ParserConfig)
        self._active_config = config
        self.update_tracer()
        try:
            if isinstance(text, Tokenizer):
                tokenizer = text
            elif issubclass(config.tokenizercls, NullTokenizer):
                tokenizer = TextLinesTokenizer(text=text, config=config, **settings)
            elif text is not None:
                cls = self.tokenizercls
                tokenizer = cls(str(text), config=config, **settings)
            else:
                raise ParseError('No tokenizer or text')  # type: ignore  # pyright: ignore[reportUnreachable]
            assert not isinstance(tokenizer, NullTokenizer)
            self.tokenizer = tokenizer
            self._states = ParseStateStack(cursor=tokenizer.newcursor())
            assert not isinstance(self.state.cursor, NullCursor)
            self._reset(config)

            if self.config.semantics and hasattr(self.config.semantics, 'set_context'):
                self.config.semantics.set_context(self)

            start: str = self.config.effective_start_rule_name() or 'start'
            rule = self.find_rule(start)
            return rule(self)

        except FailedParse as e:
            self._set_furthest_exception(e)
            if isinstance(self._furthest_exception, Exception):
                raise self._furthest_exception from e
            raise
        finally:
            self._initialize_caches()
            self._active_config = self._config
            self.update_tracer()
            if self.config.semantics and hasattr(self.config.semantics, 'set_context'):
                self.config.semantics.set_context(None)

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
        self.states.push(pos=self.pos, ast=ast)

    def popstate(self) -> ParseState:
        return self.states.pop(self.pos)

    def mergestate(self) -> ParseState:
        return self.states.merge(pos=self.pos)

    def undostate(self) -> None:
        self.states.pop()

    def _cut(self) -> None:
        self.states.set_cut_seen()
        self.tracer.trace_cut(self.cursor)

        def prune(cache: dict[Any, Any], cut_pos: int) -> None:
            prune_dict(
                cache,
                lambda k, v: k[0] < cut_pos and not isinstance(v, FailedLeftRecursion),
            )

        if self.config.prune_memos_on_cut:
            prune(self._memos, self.pos)

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

    def _save_result(self, key: MemoKey, result: RuleResult) -> None:
        if is_list(result.node):
            result = result._replace(node=closure(result.node))
        self._results[key] = result

    def _set_left_recursion_guard(self, key: MemoKey) -> None:
        if not self.config.left_recursion:
            return
        ex = self.newexcept(key.ruleinfo.name, excls=FailedLeftRecursion)
        self.memoize(key, ex)

    def call(self, ri: RuleInfo) -> Any:
        self.ruleinfo_stack.append(ri)
        self.next_token(ri)
        key: MemoKey = self.memokey()

        pos = self.pos
        try:
            self.tracer.trace_entry(self.cursor)

            if ri.is_lrec:
                result = self.recursive_call(ri, key)
            else:
                result = self.rule_call(ri, key)

            self.goto(result.newpos)
            self.states.append(result.node)

            self.tracer.trace_success(self.cursor)

            return result.node
        except FailedParse as e:
            self.goto(pos)
            self._set_furthest_exception(e)
            self.tracer.trace_failure(self.cursor, e)
            raise
        finally:
            self.ruleinfo_stack.pop()

    def _clear_recursion_errors(self) -> None:
        def filter_func(_key: MemoKey, value: Any) -> bool:
            return isinstance(value, FailedLeftRecursion)

        prune_dict(self._memos, filter_func)

    def recursive_call(self, ri: RuleInfo, key: MemoKey) -> RuleResult:
        if not ri.is_lrec:
            return self.rule_call(ri, key)
        elif not self.config.left_recursion:
            raise self.newexcept('Left recursion detected', excls=FailedLeftRecursion)

        result: RuleResult | ParseException | None = self._results.get(key)
        if isinstance(result, RuleResult):
            return result
        elif isinstance(result, Exception):
            raise result

        result = self.newexcept(ri.name, FailedLeftRecursion)
        assert isinstance(result, RuleResult | ParseException)
        self._results[key] = result

        initial = self.pos
        lastpos = -1
        while True:
            self._clear_recursion_errors()
            try:
                new_result = self.rule_call(ri, key)
                self.goto(initial)
            except FailedParse:
                break

            if new_result.newpos > lastpos:
                self._save_result(key, new_result)
                lastpos = new_result.newpos
                result = new_result
            else:
                break

        if isinstance(result, Exception):
            raise result

        assert isinstance(result, RuleResult | ParseException)
        return result

    def rule_call(self, ri: RuleInfo, key: MemoKey) -> RuleResult:
        result = self._memos.get(key)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, RuleResult):
            return result

        self._set_left_recursion_guard(key)

        self.pushstate(ast=AST())
        try:
            self.next_token(ri)

            node = self.func_call(ri)
            node = self.semantics_call(ri, node)
            self._set_parseinfo(node, ri.name, key.pos)

            result = RuleResult(node, self.pos)
            self.memoize(key, result)

            return result
        except FailedSemantics as e:
            ex = self.newexcept(str(e))
            self.memoize(key, ex)
            raise ex from e
        except ParseException as e:
            self.memoize(key, e)
            raise
        finally:
            self.undostate()

    def func_call(self, ri: RuleInfo) -> Any:
        is_legacy_parser = ri.instance is self
        with self.states.cutscope():
            if is_legacy_parser:
                ri.func(ri.instance)
            elif inspect.ismethod(ri.func):
                ri.func(self)
            else:
                ri.func(ri.instance, self)
        return self.state.node

    def semantics_call(self, ri: RuleInfo, node: Any) -> Any:
        if ri.is_name:
            self._check_name(node)

        action = self.find_semantic_action(ri.name)
        if action:
            return boundcall(action, {}, node, *ri.params, **ri.kwparams)
        else:
            return node

    def _check_name(self, name: Any) -> None:
        name_str = str(name)
        if self.config.ignorecase:
            name_str = name_str.upper()
        if name_str in self.keywords:
            raise self.newexcept(f'"{name_str}" is a reserved word', KeywordError)

    def _make_parseinfo(self, name: str, pos: int) -> ParseInfo:
        endpos = self.pos
        return ParseInfo(
            cursor=self.cursor,
            rule=name,
            pos=pos,
            endpos=endpos,
            line=self.cursor.posline(pos),
            endline=self.cursor.posline(endpos),
            alerts=self.state.alerts,
        )

    def _set_parseinfo(self, node: Any, name: str, pos: int):
        if not self.config.parseinfo:
            return
        if hasattr(node, 'set_parseinfo'):
            parseinfo = self._make_parseinfo(name, pos)
            node.set_parseinfo(parseinfo)
        elif hasattr(node, 'parseinfo'):
            parseinfo = self._make_parseinfo(name, pos)
            node.parseinfo = parseinfo

    def _constant(self, literal: Any) -> Any:
        self.next_token()
        self.tracer.trace_match(self.cursor, literal)

        if not isinstance(literal, str):
            self.states.append(literal)
            return literal
        literal = str(literal)  # for type linters

        context: dict[str, Any] = (
            safe_builtins()
            | getattr(self.semantics, 'safe_context', lambda: {})()
            | self.ast
            if isinstance(self.ast, AST)
            else {}
        )

        expression = Undefined
        result = literal
        while result != expression:
            expression = result
            if not isinstance(expression, str):
                break

            expression = trim(expression)
            with suppress(ValueError, SyntaxError):
                result = stdlib_ast.literal_eval(expression.strip())
                assert result is not Undefined
                continue

            try:
                fstr_expression = f'''f{expression!r}'''

                if is_eval_safe(fstr_expression, context):
                    result = safe_eval(fstr_expression, context)

                if result == expression and is_eval_safe(expression, context):
                    # NOTE: No f'{xyz}' evaluations occurred
                    result = safe_eval(expression, context)
            except Exception as e:
                raise FailedSemantics(
                    f'Error evaluating constant {literal!r}: {e}',
                ) from e

        self.states.append(result)
        return result
