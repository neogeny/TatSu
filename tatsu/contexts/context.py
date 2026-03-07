# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager, suppress
from typing import Any

from tatsu.ast import AST
from tatsu.util.string import regexpp

from ..exceptions import (
    FailedExpectingEndOfText,
    FailedLookahead,
    FailedParse,
    FailedPattern,
    FailedToken,
    OptionSucceeded,
    ParseException,
)
from ..util import deprecated, is_list, left_assoc, right_assoc
from ._core import Engine, closure
from .ctxlib import ChoiceContext, InnerExpContext
from .protocol import Ctx


class ParseContext(Engine, Ctx):
    # bw compatibility
    @deprecated(replacement=Engine.newexcept)
    def _error(
        self,
        item: Any,
        exclass: type[FailedParse] = FailedParse,
    ) -> FailedParse:
        raise self.newexcept(item, exclass)

    # bw compatibility
    @deprecated(replacement=Engine.setname)
    def name_last_node(self, name: str):  # bw-compat
        self.setname(name)

    # bw compatibility
    @deprecated(replacement=Engine.addname)
    def add_last_node_to_name(self, name: str):  # bw-compat
        self.addname(name)

    def _fail(self):
        self.next_token()
        raise self.newexcept('fail')

    def fail(self):
        self.next_token()
        raise self.newexcept('fail')

    def cut(self) -> None:
        self._cut()

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

    def alert(self, message: str, level: int) -> None:
        self.next_token()
        self.tracer.trace_match(
            self.cursor,
            f'{"^" * level}`{message}`',
            failed=True,
        )
        self.states.alert(level=level, message=message)

    def _alert(self, message: str, level: int) -> None:
        self.alert(message, level)

    def _pattern(self, pattern: str) -> Any:
        token = self.cursor.matchre(pattern)
        if token is None:
            self.tracer.trace_match(self.cursor, '', pattern, failed=True)
            raise self.newexcept(f'Expecting {regexpp(pattern)}', excls=FailedPattern)
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

    def _void(self) -> Any:
        self.next_token()
        return ()

    def void(self) -> Any:
        self.next_token()
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
