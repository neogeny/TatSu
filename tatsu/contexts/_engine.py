# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import ast as stdlib_ast
import inspect
from contextlib import suppress
from typing import Any

from ..config import ParserConfig
from ..exceptions import (
    FailedLeftRecursion,
    FailedParse,
    FailedSemantics,
    KeywordError,
    ParseException,
)
from ..input import NullCursor, NullText, Text
from ..input.textlines import TextLines
from ..objectmodel import ModelBuilderSemantics
from ..util import (
    Undefined,
    boundcall,
    is_eval_safe,
    prune_dict,
    safe_builtins,
    safe_eval,
    trim,
)
from ._base import ParserCore
from .ast import AST
from .cst import closedlist, islist
from .ctx import CanParse
from .infos import MemoKey, ParseInfo, RuleInfo, RuleResult
from .state import ParseStateStack


type RuleOutcome = RuleResult | ParseException
type MemoCache = dict[MemoKey, RuleOutcome]


class ParserEngine(ParserCore, CanParse):
    def parse(
        self,
        text: str | Text,
        /,
        *,
        start: str | None = None,
        config: Any = None,
        asmodel: bool = False,
        **settings: Any,
    ) -> Any:
        config = self.config.override_config(config)
        assert isinstance(config, ParserConfig)
        config = config.override(start=start, **settings)
        assert isinstance(config, ParserConfig)
        self._active_config = config
        self.update_tracer()
        try:
            if isinstance(text, Text):
                input = text
            else:
                input = TextLines(text=text, config=config)
            assert not isinstance(input, NullText)
            self.input = input
            self.states = ParseStateStack(cursor=input.newcursor())
            assert not isinstance(self.state.cursor, NullCursor)
            self._reset()

            if not self.config.semantics and asmodel:
                self.config.semantics = ModelBuilderSemantics()
            if self.config.semantics and hasattr(self.config.semantics, 'set_context'):
                self.config.semantics.set_context(self)  # ty: ignore[call-non-callable]

            actual_start: str = self.config.effective_start_rule_name() or 'start'
            rule = self.find_rule(actual_start)
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
                self.config.semantics.set_context(None)  # ty: ignore[call-non-callable]

    def call(self, ri: RuleInfo) -> Any:
        if ri.should_trace:
            self.callstack.append(ri)
        self.next_token(ri)
        key = self.memokey()

        pos = self.pos
        try:
            self.tracer.trace_entry(self)

            if ri.is_lrec:
                result = self.recursive_call(ri, key)
            else:
                result = self.rule_call(ri, key)

            self.goto(result.newpos)
            self.state.append(result.node)

            self.tracer.trace_success(self)

            return result.node
        except FailedParse as e:
            self.goto(pos)
            self.set_furthest_exception(e)
            self.tracer.trace_failure(self, e)
            raise
        finally:
            if ri.should_trace:
                self.callstack.pop()

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
        result = self.memo(key)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, RuleResult):
            return result

        self.set_left_recursion_guard(key)

        self.states.new()
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
            self.states.undo()

    def func_call(self, ri: RuleInfo) -> Any:
        with self.statescope():
            is_legacy_parser = ri.instance is self
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
                action,
                {},
                node,
                *ri.params,
                parseinfo=parseinfo,
                **ri.kwparams,
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
            line=self.cursor.lineat(pos),
            endline=self.cursor.lineat(endpos),
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
        if islist(result.node):
            result = result._replace(node=closedlist(result.node))
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

    def constant(self, literal: Any, capture: bool = True) -> Any:
        self.next_token()
        self.tracer.trace_match(self, literal)

        if not isinstance(literal, str):
            self.state.append(literal)
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

        if capture:
            self.state.append(result)
        return result

    _constant = constant
