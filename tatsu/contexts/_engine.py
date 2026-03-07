# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast as stdlib_ast
import inspect
from contextlib import suppress
from typing import Any

from ..ast import AST
from ..exceptions import (
    FailedLeftRecursion,
    FailedParse,
    FailedSemantics,
    KeywordError,
    ParseError,
    ParseException,
)
from ..infos import ParseInfo, ParserConfig
from ..tokenizing import NullCursor, NullTokenizer, Tokenizer
from ..tokenizing.textlines import TextLinesTokenizer
from ..util import (
    Undefined,
    boundcall,
    is_eval_safe,
    is_list,
    prune_dict,
    safe_builtins,
    safe_eval,
    trim,
)
from ._core import ParserCore
from .infos import MemoKey, RuleInfo, RuleResult, closure
from .state import ParseStateStack


type RuleOutcome = RuleResult | ParseException
type MemoCache = dict[MemoKey, RuleOutcome]


class ParserEngine(ParserCore):
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
            self.set_furthest_exception(e)
            if isinstance(self._furthest_exception, Exception):
                raise self._furthest_exception from e
            raise
        finally:
            self._initialize_caches()
            self._active_config = self._config
            self.update_tracer()
            if self.config.semantics and hasattr(self.config.semantics, 'set_context'):
                self.config.semantics.set_context(None)

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
            self.set_furthest_exception(e)
            self.tracer.trace_failure(self.cursor, e)
            raise
        finally:
            self.ruleinfo_stack.pop()

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
            self.clear_recursion_errors()
            try:
                new_result = self.rule_call(ri, key)
                self.goto(initial)
            except FailedParse:
                break

            if new_result.newpos > lastpos:
                self.save_result(key, new_result)
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

        self.set_left_recursion_guard(key)

        self.pushstate(ast=AST())
        try:
            self.next_token(ri)

            node = self.func_call(ri)
            node = self.semantics_call(ri, node, pos=key.pos)
            self.set_parseinfo(node, ri.name, key.pos)

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

    def semantics_call(self, ri: RuleInfo, node: Any, pos: int) -> Any:
        if ri.is_name:
            self.validate_is_not_keyword(node)

        action = self.find_semantic_action(ri.name)
        if action:
            parseinfo = self.make_parseinfo(node, pos)
            return boundcall(
                action, {}, node, *ri.params, parseinfo=parseinfo, **ri.kwparams,
            )
        else:
            return node

    def validate_is_not_keyword(self, name: Any) -> None:
        name_str = str(name)
        if self.config.ignorecase:
            name_str = name_str.upper()
        if name_str in self.keywords:
            raise self.newexcept(f'"{name_str}" is a reserved word', KeywordError)

    def make_parseinfo(self, name: str, pos: int) -> ParseInfo | None:
        if not self.config.parseinfo:
            return None
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

    def set_parseinfo(self, node: Any, name: str, pos: int):
        parseinfo = self.make_parseinfo(name, pos)
        if parseinfo is None:
            return
        elif hasattr(node, 'set_parseinfo'):
            node.set_parseinfo(parseinfo)
        elif hasattr(node, 'parseinfo'):
            node.parseinfo = parseinfo

    def save_result(self, key: MemoKey, result: RuleResult) -> None:
        if is_list(result.node):
            result = result._replace(node=closure(result.node))
        self._results[key] = result

    def set_left_recursion_guard(self, key: MemoKey) -> None:
        if not self.config.left_recursion:
            return
        ex = self.newexcept(key.ruleinfo.name, excls=FailedLeftRecursion)
        self.memoize(key, ex)

    def clear_recursion_errors(self) -> None:
        def filter_func(_key: MemoKey, value: Any) -> bool:
            return isinstance(value, FailedLeftRecursion)

        prune_dict(self._memos, filter_func)

    def cut(self) -> None:
        self.states.set_cut_seen()
        self.tracer.trace_cut(self.cursor)

        def prune(cut_pos: int) -> None:
            prune_dict(
                self._memos,
                lambda k, v: k[0] < cut_pos and not isinstance(v, FailedLeftRecursion),
            )

        if self.config.prune_memos_on_cut:
            prune(self.pos)

    def constant(self, literal: Any) -> Any:
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

    _constant = constant
