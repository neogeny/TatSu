# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast as stdlib_ast
import inspect
from collections.abc import Callable, Generator
from contextlib import contextmanager, suppress
from functools import cache
from typing import Any

from .. import buffering
from ..ast import AST
from ..buffering import Buffer
from ..collections import BoundedDict
from ..exceptions import (
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
from ..infos import Alert, ParseInfo, ParserConfig
from ..tokenizing import Cursor, NullCursor, NullTokenizer, Tokenizer
from ..tokenizing.textlines import TextLinesTokenizer
from ..util import regexp, safe_name, trim
from ..util.abctools import is_list, left_assoc, prune_dict, right_assoc
from ..util.deprecate import deprecated
from ..util.safeeval import is_eval_safe, safe_builtins, safe_eval
from ..util.typetools import boundcall
from ..util.undefined import Undefined
from .ctxlib import ChoiceContext, InnerExpContext
from .infos import MemoKey, RuleInfo, RuleResult, closure
from .protocol import Ctx
from .state import ParseState, ParseStateStack
from .tracing import EventTracer, InfoEventTracer, NullEventTracer


__all__: list[str] = ['ParseContext']


type RuleOutcome = RuleResult | ParseException
type MemoCache = dict[MemoKey, RuleOutcome]


@cache
def find_cached_semantic_action(semantics: Any, name: str) -> Callable[..., Any] | None:
    if not semantics:
        return None

    for rulename in (name, name.strip('_'), f'_{name}', f'_{name}_'):
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


class ParseContext(Ctx):
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
        if config.tokenizercls is None:
            config = config.override(tokenizercls=TextLinesTokenizer)
        assert isinstance(config, ParserConfig)
        self._config: ParserConfig = config
        self._active_config: ParserConfig = self._config

        self._tokenizer: Tokenizer = NullTokenizer()
        self._cursor = self._tokenizer.newcursor()
        self._semantics: type | None = config.semantics
        self._states: ParseStateStack = ParseStateStack(cursor=self._cursor)

        self._initialize_caches()
        self._tracer: EventTracer = NullEventTracer()
        self.update_tracer()

    def _initialize_caches(self) -> None:
        self._furthest_exception: FailedParse | None = None
        self._memos: MemoCache = BoundedDict(self.config.memo_cache_size)
        self._results: MemoCache = {}
        self._states = ParseStateStack(cursor=self.tokenizer.newcursor())

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

    @property
    def tokenizer(self) -> Tokenizer:
        return self._tokenizer

    @property
    def cursor(self) -> Cursor:
        return self.state.cursor

    @property
    def tokenizercls(self) -> type[Tokenizer]:
        if self.config.tokenizercls is None:
            return buffering.Buffer
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
        self._tracer = tracer
        return self.tracer

    def _reset(self, config: ParserConfig) -> ParserConfig:
        self._initialize_caches()
        self._keywords: set[str] = set(config.keywords)
        self._semantics = config.semantics
        if hasattr(self.semantics, 'set_context'):
            self.semantics.set_context(self)
        return config

    def _set_furthest_exception(self, e: FailedParse) -> None:
        if not self._furthest_exception or e.pos > self._furthest_exception.pos:
            self._furthest_exception = e

    def parse(
        self,
        text: str | Tokenizer,
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
                tokenizer = Buffer(text=text, config=config, **settings)
            elif text is not None:
                cls = self.tokenizercls
                tokenizer = cls(text, config=config, **settings)
            else:
                raise ParseError('No tokenizer or text')
            assert not isinstance(tokenizer, NullTokenizer)
            self._tokenizer = tokenizer
            self._cursor = self._tokenizer.newcursor()
            self._states = ParseStateStack(cursor=tokenizer.newcursor())
            assert not isinstance(self._cursor, NullCursor)
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

    # bw compatibility
    @deprecated(replacement=setname)
    def name_last_node(self, name: str):  # bw-compat
        self.setname(name)

    # bw compatibility
    @deprecated(replacement=addname)
    def add_last_node_to_name(self, name: str):  # bw-compat
        self.addname(name)

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

    def cut(self) -> None:
        self._cut()

    def _memoization(self) -> bool:
        if not self.config.memoization:
            return False
        return self.config.memoize_lookaheads or self.lookahead == 0

    def find_rule(self, name: str) -> Callable[..., Any]:
        raise NotImplementedError

    def _find_semantic_action(self, name: str) -> Callable[..., Any] | None:
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

    # bw compatibility
    @deprecated(replacement=newexcept)
    def _error(
        self,
        item: Any,
        exclass: type[FailedParse] = FailedParse,
    ) -> FailedParse:
        raise self.newexcept(item, exclass)

    def _fail(self):
        raise self.newexcept('fail')

    def fail(self):
        raise self.newexcept('fail')

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

    @property
    def ruleinfo(self) -> RuleInfo:
        return self.ruleinfo_stack[-1]

    def memokey(self) -> MemoKey:
        return MemoKey(self.pos, self.ruleinfo)

    def _memoize(
        self,
        key: MemoKey,
        memo: RuleResult | ParseException,
    ) -> RuleResult | ParseException:
        if self._memoization() and key.ruleinfo.is_memo:
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
        self._memoize(key, ex)

    def call(self, ri: RuleInfo) -> Any:
        self.ruleinfo_stack.append(ri)
        self.next_token(ri)
        key: MemoKey = self.memokey()

        pos = self.pos
        try:
            self.tracer.trace_entry(self.cursor)

            if ri.is_lrec:
                result = self._recursive_call(ri, key)
            else:
                result = self._rule_call(ri, key)

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

    def _recursive_call(self, ri: RuleInfo, key: MemoKey) -> RuleResult:
        if not ri.is_lrec:
            return self._rule_call(ri, key)
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
                new_result = self._rule_call(ri, key)
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

    def _rule_call(self, ri: RuleInfo, key: MemoKey) -> RuleResult:
        result = self._memos.get(key)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, RuleResult):
            return result

        self._set_left_recursion_guard(key)

        self.pushstate(ast=AST())
        try:
            self.next_token(ri)

            node = self._func_call(ri)
            node = self._semantics_call(ri, node)
            self._set_parseinfo(node, ri.name, key.pos)

            result = RuleResult(node, self.pos)
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
            self.undostate()

    def _func_call(self, ri: RuleInfo) -> Any:
        is_legacy_parser = ri.instance is self
        with self.states.cutscope():
            if is_legacy_parser:
                ri.func(ri.instance)
            elif inspect.ismethod(ri.func):
                ri.func(self)
            else:
                ri.func(ri.instance, self)
        return self.state.node

    def _semantics_call(self, ri: RuleInfo, node: Any) -> Any:
        if ri.is_name:
            self._check_name(node)

        action = self._find_semantic_action(ri.name)
        if action:
            return boundcall(action, {}, node, *ri.params, **ri.kwparams)
        else:
            return node

    def token(self, token: str) -> str:
        self.next_token()
        if self.cursor.match(token) is None:
            self.tracer.trace_match(self.cursor, token, failed=True)
            raise self.newexcept(token, excls=FailedToken)
        self.tracer.trace_match(self.cursor, token)
        self.states.append(token)
        return token

    def _token(self, token: str) -> str:
        return self.token(token)

    def constant(self, literal: Any) -> Any:
        return self._constant(literal)

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

    def alert(self, message: str, level: int) -> None:
        self.next_token()
        self.tracer.trace_match(
            self.cursor,
            f'{"^" * level}`{message}`',
            failed=True,
        )
        self.state.alerts.append(Alert(message=message, level=level))

    def _alert(self, message: str, level: int) -> None:
        self.alert(message, level)

    def _pattern(self, pattern: str) -> Any:
        token = self.cursor.matchre(pattern)
        if token is None:
            self.tracer.trace_match(self.cursor, '', pattern, failed=True)
            raise self.newexcept(f'Expecting {regexp(pattern)}', excls=FailedPattern)
        self.tracer.trace_match(self.cursor, token, pattern)
        self.states.append(token)
        return token

    def pattern(self, pattern: str) -> Any:
        return self._pattern(pattern)

    def eof(self) -> bool:
        return self.cursor.atend()

    def eol(self) -> bool:
        return self.cursor.ateol()

    def _check_eof(self) -> None:
        self.next_token()
        if not self.cursor.atend():
            raise self.newexcept(
                'Expecting end of text',
                excls=FailedExpectingEndOfText,
            )

    def eofcheck(self) -> None:
        self._check_eof()

    @contextmanager
    def _try(self) -> Any:
        self.pushstate(ast=AST(self.ast))
        try:
            yield
            self.mergestate()
        except FailedParse:
            self.undostate()
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
    def option(self) -> Any:
        try:
            with self._try():
                yield
            raise OptionSucceeded()
        except FailedParse:
            if not self.states.cut_seen():
                pass
            else:
                raise

    @contextmanager
    def _option(self) -> Any:
        with self.option():
            yield

    @contextmanager
    def choice(self) -> Generator[ChoiceContext, Any, Any]:
        ctx = ChoiceContext(self)
        with suppress(OptionSucceeded), self.states.cutscope():
            yield ctx
            ctx.run()

    @contextmanager
    def _choice(self) -> Generator[ChoiceContext, Any, Any]:
        with self.choice() as ch:
            yield ch

    @contextmanager
    def _optional(self) -> Any:
        with self._choice(), self._option(), self.states.cutscope():
            yield

    @contextmanager
    def optional(self) -> Any:
        with self._choice(), self._option(), self.states.cutscope():
            yield

    @contextmanager
    def group(self) -> Any:
        self.pushstate()
        try:
            with self.states.cutscope():
                yield
            self.mergestate()
        except ParseException:
            self.undostate()
            raise

    @contextmanager
    def _group(self) -> Any:
        with self.group():
            yield

    @contextmanager
    def if_(self) -> Any:
        self.pushstate()
        self.lookahead += 1
        try:
            yield
        finally:
            self.undostate()
            self.lookahead -= 1

    @contextmanager
    def ifnot_(self) -> Any:
        try:
            with self.if_():
                yield
        except ParseException:
            pass
        else:
            raise self.newexcept('', excls=FailedLookahead)

    @contextmanager
    def _if(self) -> Any:
        with self.if_():
            yield

    @contextmanager
    def _ifnot(self) -> Any:
        with self.ifnot_():
            yield

    @contextmanager
    def _setname(self, name: str) -> Any:
        yield
        self.setname(name)

    @contextmanager
    def nameset(self, name: str) -> Any:
        yield
        self.setname(name)

    @contextmanager
    def _addname(self, name: str) -> Any:
        yield
        self.addname(name)

    @contextmanager
    def nameadd(self, name: str) -> Any:
        yield
        self.addname(name)

    def _isolate(self, exp: Callable[[], Any], _drop: bool = False) -> Any:
        self.pushstate()
        try:
            exp()
            return closure(self.cst) if is_list(self.cst) else self.cst
        finally:
            ast = self.ast
            self.popstate()
            self.ast = ast

    def _repeat(
        self,
        exp: Callable[[], Any],
        prefix: Callable[[], Any] | None = None,
        dropprefix: bool = False,
    ) -> None:
        while True:
            with self._choice():
                with self._option():
                    p = self.pos

                    if prefix:
                        pcst = self._isolate(prefix, _drop=dropprefix)
                        if not dropprefix:
                            self.states.append(pcst)
                        self._cut()

                    cst = self._isolate(exp)
                    self.states.append(cst)

                    if self.pos == p:
                        raise self.newexcept('empty closure')
                return

    @contextmanager
    def loopopt(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._closure(cl._exp_value())

    @contextmanager
    def loopplus(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._positive_closure(cl._exp_value())

    def _closure(
        self,
        exp: Callable[[], Any],
        sep: Callable[[], Any] | None = None,
        omitsep: bool = False,
    ) -> Any:
        self.pushstate()
        try:
            self.cst = []
            with self.states.cutscope():
                with self._optional():
                    exp()
                    self.cst = [self.cst]
                self._repeat(exp, prefix=sep, dropprefix=omitsep)
            self.cst = closure(self.cst)
            return self.mergestate().cst
        except ParseException:
            self.undostate()
            raise

    def _positive_closure(
        self,
        exp: Callable[[], Any],
        sep: Callable[[], Any] | None = None,
        omitsep: bool = False,
    ) -> Any:
        self.pushstate()
        try:
            with self.states.cutscope():
                exp()
                self.cst = [self.cst]
                self._repeat(exp, prefix=sep, dropprefix=omitsep)
            self.cst = closure(self.cst)
            return self.mergestate().cst
        except ParseException:
            self.undostate()
            raise

    def empty(self) -> list:
        cst = closure([])
        self.states.append(cst)
        return cst

    def _empty_closure(self) -> list:
        return self.empty()

    @contextmanager
    def gatheropt(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._gather(cl._exp_value(), cl._sep_value())

    @contextmanager
    def gatherplus(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._positive_gather(cl._exp_value(), cl._sep_value())

    def _gather(self, exp: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._closure(exp, sep=sep, omitsep=True)

    def _positive_gather(self, exp: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._positive_closure(exp, sep=sep, omitsep=True)

    @contextmanager
    def joinopt(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._join(cl._exp_value(), cl._sep_value())

    @contextmanager
    def joinplus(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._positive_join(cl._exp_value(), cl._sep_value())

    def _join(self, exp: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._closure(exp, sep=sep)

    def _positive_join(self, exp: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        return self._positive_closure(exp, sep=sep)

    @contextmanager
    def joinleft(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._left_join(cl._exp_value(), cl._sep_value())

    @contextmanager
    def joinright(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._right_join(cl._exp_value(), cl._sep_value())

    def _left_join(self, exp: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        self.cst = left_assoc(self._positive_join(exp, sep))
        return self.cst

    def _right_join(self, exp: Callable[[], Any], sep: Callable[[], Any]) -> Any:
        self.cst = right_assoc(self._positive_join(exp, sep))
        return self.cst

    def _check_name(self, name: Any) -> None:
        name_str = str(name)
        if self.config.ignorecase:
            name_str = name_str.upper()
        if name_str in self.keywords:
            raise self.newexcept(f'"{name_str}" is a reserved word', KeywordError)

    def _void(self) -> None:
        pass

    def void(self) -> Any:
        return ()

    def dot(self) -> Any:
        c = self._next()
        if c is None:
            self.tracer.trace_match(self.cursor, c, failed=True)
            raise self.newexcept(c, excls=FailedToken) from None
        self.tracer.trace_match(self.cursor, c)
        self.states.append(c)
        return c

    def _dot(self) -> Any:
        return self.dot()

    @contextmanager
    def _skipto(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._skip_to(cl._exp_value())

    @contextmanager
    def skipto(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self._skip_to(cl._exp_value())

    def _skip_to(self, exp: Callable[[], Any]) -> Any:
        while not self.eof():
            try:
                with self.if_():
                    exp()
            except FailedParse:
                pass
            else:
                break
            pos = self.pos
            self.next_token()
            if self.pos == pos:
                self._next()
        return exp()
