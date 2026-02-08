# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast as stdlib_ast
import inspect
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager, suppress
from typing import Any

from .. import buffering, tokenizing
from ..ast import AST
from ..buffering import Buffer
from ..collections import BoundedDict
from ..exceptions import (
    FailedCut,
    FailedExpectingEndOfText,
    FailedLeftRecursion,
    FailedLookahead,
    FailedParse,
    FailedPattern,
    FailedSemantics,
    FailedToken,
    KeywordError,
    OptionSucceeded,
    ParseError,
    ParseException,
)
from ..infos import (
    Alert,
    ParseInfo,
    ParserConfig,
    RuleInfo,
)
from ..tokenizing import NullTokenizer, Tokenizer
from ..util import (
    Undefined,
    safe_name,
    trim,
)
from ..util.abctools import is_list, left_assoc, prune_dict, right_assoc
from ..util.safeeval import is_eval_safe, safe_builtins, safe_eval
from .infos import MemoKey, RuleResult, closure
from .state import ParseState, ParseStateStack
from .tracing import EventTracer, EventTracerImpl

__all__: list[str] = ['ParseContext']


class ParseContext:
    def __init__(self, /, config: ParserConfig | None = None, **settings: Any) -> None:
        super().__init__()

        config = ParserConfig.new(config, **settings)
        if config.tokenizercls is None:
            config = config.override(tokenizercls=Buffer)
        self._config: ParserConfig = config
        self._active_config: ParserConfig = self._config

        self._tokenizer: Tokenizer = NullTokenizer()
        self._semantics: type | None = config.semantics
        self._initialize_caches()

        self._tracer: EventTracer = EventTracer()
        self.update_tracer()

    def _initialize_caches(self) -> None:
        self._states = ParseStateStack()
        self._ruleinfo_stack: list[RuleInfo] = []

        self.substate: Any = None
        self._lookahead: int = 0
        self._furthest_exception: FailedParse | None = None

        self._clear_memoization_caches()

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
    def semantics(self) -> Any:
        return self._semantics

    @property
    def keywords(self) -> set[str]:
        return self._keywords

    @property
    def tracer(self):
        return self._tracer

    def update_tracer(self) -> EventTracer:
        tracer = EventTracerImpl(
            self._tokenizer,
            self._ruleinfo_stack,
            config=self.config,
        )
        self._tracer = tracer
        return self.tracer

    def _reset(self, config: ParserConfig) -> ParserConfig:
        self._initialize_caches()
        self._keywords: set[str] = set(config.keywords)
        self._semantics = config.semantics
        if hasattr(self.semantics, 'set_context'):
            self.semantics.set_context(self)
        return config

    def _clear_memoization_caches(self) -> None:
        self._memos: BoundedDict[MemoKey, RuleResult | ParseException] = BoundedDict(self.config.memo_cache_size)
        self._results: dict[MemoKey, RuleResult | ParseException] = {}

    def _set_furthest_exception(self, e: FailedParse) -> None:
        if (
                not self._furthest_exception
                or e.pos > self._furthest_exception.pos
        ):
            self._furthest_exception = e

    def parse(self, text: str | Tokenizer, /, *, config: ParserConfig | None = None, **settings: Any) -> Any:
        config = self.config.override_config(config)
        config = config.override(**settings)
        self._active_config = config
        self.update_tracer()
        try:
            self._reset(config)
            if isinstance(text, tokenizing.Tokenizer):
                tokenizer = text
            elif issubclass(config.tokenizercls, NullTokenizer):
                tokenizer = Buffer(text=text, config=config, **settings)
            elif text is not None:
                cls = self.tokenizercls
                tokenizer = cls(text, config=config, **settings)
            else:
                raise ParseError('No tokenizer or text')
            self._tokenizer = tokenizer

            if self.config.semantics and hasattr(self.config.semantics, 'set_context'):
                self.config.semantics.set_context(self)

            start: str = self.config.effective_rule_name() or 'start'
            rule = self._find_rule(start)
            return rule()

        except FailedParse as e:
            self._set_furthest_exception(e)
            if isinstance(self._furthest_exception, Exception):
                raise self._furthest_exception from e
            raise
        finally:
            self._clear_memoization_caches()
            self._active_config = self._config
            self.update_tracer()
            if self.config.semantics and hasattr(self.config.semantics, 'set_context'):
                self.config.semantics.set_context(None)

    @property
    def tokenizer(self) -> Tokenizer:
        return self._tokenizer

    @property
    def tokenizercls(self) -> type[Tokenizer]:
        if self.config.tokenizercls is None:
            return buffering.Buffer
        else:
            return self.config.tokenizercls

    @property
    def last_node(self) -> Any:
        return self.states.last_node

    @last_node.setter
    def last_node(self, value: Any) -> None:
        self.states.last_node = value

    @property
    def pos(self) -> int:
        return self._tokenizer.pos

    @property
    def line(self) -> int:
        return self._tokenizer.line

    def goto(self, pos: int) -> None:
        self._tokenizer.goto(pos)

    def _next(self) -> Any:
        return self._tokenizer.next()

    def next_token(self, ruleinfo: RuleInfo | None = None) -> None:
        if not (ruleinfo and ruleinfo.is_token_rule()):
            self._tokenizer.next_token()

    def _define(self, keys: Iterable[str], list_keys: Iterable[str] | None = None) -> None:
        # NOTE: called by generated parsers
        return self.states.define(keys, list_keys)

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

    def name_last_node(self, name: str) -> None:
        # NOTE: called by generated parsers
        self.states.name_last_node(name)

    def add_last_node_to_name(self, name: str) -> None:
        # NOTE: called by generated parsers
        self.states.add_last_node_to_name(name)

    def _push_ast(self, copyast: bool = False) -> Any:
        return self.states.push_ast(pos=self.pos, copyast=copyast)

    def _pop_ast(self) -> Any:
        ast = self.states.pop_ast()
        self.tokenizer.goto(self.state.pos)
        return ast

    def _cut(self) -> None:
        self.states.set_cut_seen()
        self.tracer.trace_cut()

        def prune(cache: dict[Any, Any], cut_pos: int) -> None:
            prune_dict(
                cache,
                lambda k, v: k[0] < cut_pos and not isinstance(v, FailedLeftRecursion),
            )

        if self.config.prune_memos_on_cut:
            prune(self._memos, self.pos)

    def _memoization(self) -> bool:
        return self.config.memoization and (
                self.config.memoize_lookaheads or
                self._lookahead == 0
        )

    def _find_rule(self, name: str) -> Callable[[], Any]:
        raise NotImplementedError

    def _find_semantic_action(self, name: str) -> tuple[Callable[..., Any] | None, Callable[..., Any] | None]:
        if self.semantics is None:
            return None, None

        postproc = getattr(self.semantics, '_postproc', None)

        action = getattr(self.semantics, safe_name(name), None)
        if not callable(action):
            action = getattr(self.semantics, '_default', None)

        if not callable(action):
            action = None
        if not callable(postproc):
            postproc = None

        return action, postproc

    def newexcept(self, item: Any, exclass: type[FailedParse] = FailedParse) -> FailedParse:
        if issubclass(exclass, FailedLeftRecursion):
            rulestack: list[str] = []
        else:
            rulestack = [r.name for r in reversed(self._ruleinfo_stack)]
        return exclass(self.tokenizer.lineinfo(), rulestack, item)

    def _fail(self):
        raise self.newexcept('fail')

    def _get_parseinfo(self, name: str, pos: int) -> ParseInfo:
        endpos = self.pos
        return ParseInfo(
            tokenizer=self.tokenizer,
            rule=name,
            pos=pos,
            endpos=endpos,
            line=self.tokenizer.posline(pos),
            endline=self.tokenizer.posline(endpos),
            alerts=self.state.alerts,
        )

    @property
    def ruleinfo(self) -> RuleInfo:
        return self._ruleinfo_stack[-1]

    def memokey(self) -> MemoKey:
        return MemoKey(self.pos, self.ruleinfo, self.substate)

    def _memoize(self, key: MemoKey, memo: RuleResult | ParseException) -> RuleResult | ParseException:
        if self._memoization() and key.ruleinfo.is_memoizable:
            self._memos[key] = memo
        return memo

    def _save_result(self, key: MemoKey, result: RuleResult) -> None:
        if is_list(result.node):
            result = result._replace(node=closure(result.node))
        self._results[key] = result

    def _set_left_recursion_guard(self, key: MemoKey) -> None:
        if not self.config.left_recursion:
            return
        ex = self.newexcept(key.ruleinfo.name, exclass=FailedLeftRecursion)
        self._memoize(key, ex)

    def _call(self, ruleinfo: RuleInfo) -> Any:
        self._ruleinfo_stack += [ruleinfo]
        pos = self.pos
        try:
            self.tracer.trace_entry()
            self.last_node = None

            result = self._recursive_call(ruleinfo)

            self.goto(result.newpos)
            self.substate = result.newstate
            self.states.append_cst(result.node)

            self.tracer.trace_success()

            return result.node
        except FailedPattern as e:
            raise self.newexcept(f'Expecting <{ruleinfo.name}>') from e
        except FailedParse as e:
            self.goto(pos)
            self._set_furthest_exception(e)
            self.tracer.trace_failure(e)
            raise
        finally:
            self._ruleinfo_stack.pop()

    def _clear_recursion_errors(self) -> None:
        def filter_func(key: MemoKey, value: Any) -> bool:
            return isinstance(value, FailedLeftRecursion)

        prune_dict(self._memos, filter_func)

    def _found_left_recursion(self, ruleinfo: RuleInfo) -> bool:
        return any(ri.name == ruleinfo.name for ri in self._ruleinfo_stack)

    def _recursive_call(self, ruleinfo: RuleInfo) -> RuleResult:
        self.next_token(ruleinfo)
        key: MemoKey = self.memokey()

        if not ruleinfo.is_leftrec:
            return self._rule_call(ruleinfo, key)
        elif not self.config.left_recursion:
            raise self.newexcept('Left recursion detected', exclass=FailedLeftRecursion)

        result: RuleResult | ParseException | None = self._results.get(key)
        if isinstance(result, RuleResult):
            return result
        elif isinstance(result, Exception):
            raise result

        result = self.newexcept(ruleinfo.name, FailedLeftRecursion)
        self._results[key] = result

        initial = self.pos
        lastpos = -1
        while True:
            self._clear_recursion_errors()
            try:
                new_result = self._rule_call(ruleinfo, key)
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

        return result

    def _asnode(self, ast: Any, cst: Any) -> Any:
        if not ast:
            return tuple(cst) if is_list(cst) else cst
        elif '@' in ast:
            return ast['@']
        else:
            return ast

    def _rule_call(self, ruleinfo: RuleInfo, key: MemoKey) -> RuleResult:
        result = self._memos.get(key)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, RuleResult):
            return result

        self._set_left_recursion_guard(key)

        self._push_ast()
        try:
            self.next_token(ruleinfo)
            ruleinfo.impl(self)
            node = self._asnode(self.ast, self.cst)
            node = self._semantics_call(ruleinfo, node)

            if self.config.parseinfo and hasattr(node, 'set_parseinfo'):
                parseinfo = self._get_parseinfo(ruleinfo.name, key.pos)
                node.set_parseinfo(parseinfo)

            result = RuleResult(node, self.pos, self.substate)
            self._memoize(key, result)

            return result
        except FailedSemantics as e:
            ex = self.newexcept(str(e))
            self._memoize(key, ex)
            raise ex from e
        except ParseException as e:
            self._memoize(key, e)
            raise
        finally:
            self._pop_ast()

    def _semantics_call(self, ruleinfo: RuleInfo, node: Any) -> Any:
        params = ruleinfo.params or ()
        kwparams = ruleinfo.kwparams or {}
        semantic, postproc = self._find_semantic_action(ruleinfo.name)
        if semantic:
            if inspect.ismethod(semantic):
                node = semantic(node, *params, **kwparams)
            else:
                node = semantic(self.semantics, node, *params, **kwparams)

        if callable(postproc):
            postproc(self, node)
        if ruleinfo.is_name:
            self._check_name(node)
        return node

    def _token(self, token: str) -> str:
        self.next_token()
        if self.tokenizer.match(token) is None:
            self.tracer.trace_match(token, failed=True)
            raise self.newexcept(token, exclass=FailedToken)
        self.tracer.trace_match(token)
        self.states.append_cst(token)
        return token

    def _constant(self, literal: Any) -> Any:
        self.next_token()
        self.tracer.trace_match(literal)

        if not isinstance(literal, str):
            self.states.append_cst(literal)
            return literal
        literal = str(literal)  # for type linters

        context: dict[str, Any] = (
            safe_builtins() |
            getattr(self.semantics, 'safe_context', lambda: {})() |
            self.ast if isinstance(self.ast, AST) else {}
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
                fstr_expression = f'f{expression!r}'

                if is_eval_safe(fstr_expression, context):
                    result = safe_eval(fstr_expression, context)

                if result == expression and is_eval_safe(expression, context):
                    # NOTE: No f'{xyz}' evaluations occurred
                    result = safe_eval(expression, context)
            except Exception as e:
                raise FailedSemantics(
                    f'Error evaluating constant {literal!r}: {e}',
                ) from e

        self.states.append_cst(result)
        return result

    def _alert(self, message: str, level: int) -> None:
        self.next_token()
        self.tracer.trace_match(f'{"^" * level}`{message}`', failed=True)
        self.state.alerts.append(Alert(message=message, level=level))

    def _pattern(self, pattern: str) -> Any:
        token = self.tokenizer.matchre(pattern)
        if token is None:
            self.tracer.trace_match('', pattern, failed=True)
            raise self.newexcept(pattern, exclass=FailedPattern)
        self.tracer.trace_match(token, pattern)
        self.states.append_cst(token)
        return token

    def eof(self) -> bool:
        return self.tokenizer.atend()

    def eol(self) -> bool:
        return self.tokenizer.ateol()

    def _check_eof(self) -> None:
        self.next_token()
        if not self.tokenizer.atend():
            raise self.newexcept(
                'Expecting end of text', exclass=FailedExpectingEndOfText,
            )

    @contextmanager
    def _try(self) -> Generator[None]:
        s = self.substate
        self._push_ast(copyast=True)
        self.last_node = None
        try:
            yield
            self.states.merge_ast()
        except FailedParse:
            self._pop_ast()
            self.substate = s
            raise

    def _no_more_options(self) -> bool:
        """
        Used by the Python code generator so there are
        no unconditional:
            ```
            raise self.newexception(...)
            ```
        that fool the syntax highlighting of editors
        """
        return True

    @contextmanager
    def _option(self) -> Generator[None]:
        self.last_node = None
        self.states.push_cut()
        try:
            with self._try():
                yield
            raise OptionSucceeded()
        except FailedCut:
            raise
        except FailedParse as e:
            if self.states.is_cut_set():
                raise FailedCut(e) from e
        finally:
            self.states.pop_cut()

    @contextmanager
    def _choice(self) -> Generator[None]:
        self.last_node = None
        with suppress(OptionSucceeded):
            try:
                yield
            except FailedCut as e:
                raise e.nested from e

    @contextmanager
    def _optional(self) -> Generator[None]:
        self.last_node = None
        with self._choice(), self._option():
            yield

    @contextmanager
    def _group(self) -> Generator[None]:
        self.states.push_cst()
        try:
            yield
            self.states.merge_cst(extend=True)
        except ParseException:
            self.states.pop_cst()
            raise

    @contextmanager
    def _if(self) -> Generator[None]:
        s = self.substate
        self._push_ast()
        self._lookahead += 1
        try:
            yield
        finally:
            self._pop_ast()  # simply discard
            self._lookahead -= 1
            self.substate = s

    @contextmanager
    def _ifnot(self) -> Generator[None]:
        try:
            with self._if():
                yield
        except ParseException:
            pass
        else:
            raise self.newexcept('', exclass=FailedLookahead)

    def _isolate(self, block: Callable[[], Any], drop: bool = False) -> Any:
        self.states.push_cst()
        try:
            block()
            cst = self.cst
        finally:
            self.states.pop_cst()

        if is_list(cst):
            cst = closure(cst)
        if not drop:
            self.states.append_cst(cst)
        return cst

    def _repeat(self, block: Callable[[], Any], prefix: Callable[[], Any] | None = None, dropprefix: bool = False) -> None:
        while True:
            with self._choice():
                with self._option():
                    p = self.pos

                    if prefix:
                        self._isolate(prefix, drop=dropprefix)
                        self._cut()

                    self._isolate(block)

                    if self.pos == p:
                        raise self.newexcept('empty closure')
                return

    def _closure(self, block: Callable[[], Any], sep: Callable[[], Any] | None = None, omitsep: bool = False) -> Any:
        self.states.push_cst()
        try:
            self.cst = []
            with self._optional():
                block()
                self.cst = [self.cst]
            self._repeat(block, prefix=sep, dropprefix=omitsep)
            self.cst = closure(self.cst)
            return self.states.merge_cst()
        except ParseException:
            self.states.pop_cst()
            raise

    def _positive_closure(self, block: Callable[[], Any], sep: Callable[[], Any] | None = None, omitsep: bool = False) -> Any:
        self.states.push_cst()
        try:
            block()
            self.cst = [self.cst]
            self._repeat(block, prefix=sep, dropprefix=omitsep)
            self.cst = closure(self.cst)
            return self.states.merge_cst()
        except ParseException:
            self.states.pop_cst()
            raise

    def _empty_closure(self) -> closure:
        cst = closure([])
        self.states.append_cst(cst)
        return cst

    def _gather(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._closure(block, sep=sep, omitsep=True)

    def _positive_gather(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._positive_closure(block, sep=sep, omitsep=True)

    def _join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._closure(block, sep=sep)

    def _positive_join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._positive_closure(block, sep=sep)

    def _left_join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        self.cst = left_assoc(self._positive_join(block, sep))
        self.last_node = self.cst
        return self.cst

    def _right_join(self, block: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        self.cst = right_assoc(self._positive_join(block, sep))
        self.last_node = self.cst
        return self.cst

    def _check_name(self, name: Any) -> None:
        name_str = str(name)
        if self.config.ignorecase or self.tokenizer.ignorecase:
            name_str = name_str.upper()
        if name_str in self.keywords:
            raise self.newexcept(
                f'"{name_str}" is a reserved word',
                KeywordError,
            )

    def _void(self) -> None:
        self.last_node = None

    def _dot(self) -> Any:
        c = self._next()
        if c is None:
            self.tracer.trace_match(c, failed=True)
            raise self.newexcept(c, exclass=FailedToken) from None
        self.tracer.trace_match(c)
        self.states.append_cst(c)
        return c

    def _skip_to(self, block: Callable[[], Any]) -> None:
        while not self.eof():
            try:
                with self._if():
                    block()
            except FailedParse:
                pass
            else:
                break
            pos = self.pos
            self.next_token()
            if self.pos == pos:
                self._next()
        block()
