# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any

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
from ..util.strtools import regexpp
from ._engine import ParserEngine
from ._protocol import Ctx, Func
from .ast import AST
from .ctxlib import ChoiceContext, InnerExpContext
from .infos import listclosure


class ParseContext(ParserEngine, Ctx):
    # bw compatibility
    @deprecated(replacement=ParserEngine.newexcept)
    def _error(
        self,
        item: Any,
        exclass: type[FailedParse] = FailedParse,
    ) -> FailedParse:
        raise self.newexcept(item, exclass)

    # bw compatibility
    @deprecated(replacement=ParserEngine.setname)
    def name_last_node(self, name: str):  # bw-compat
        self.setname(name)

    # bw compatibility
    @deprecated(replacement=ParserEngine.addname)
    def add_last_node_to_name(self, name: str):  # bw-compat
        self.addname(name)

    def fail(self):
        self.next_token()
        raise self.newexcept('fail')

    _fail = fail

    def token(self, token: str) -> str:
        self.next_token()
        if self.cursor.match(token) is None:
            self.tracer.trace_match(self.cursor, token, failed=True)
            raise self.newexcept(token, excls=FailedToken)
        self.tracer.trace_match(self.cursor, token)
        self.state.append(token)
        return token

    _token = token

    def alert(self, message: str, level: int) -> None:
        self.next_token()
        self.tracer.trace_match(
            self.cursor,
            f'{"^" * level}`{message}`',
            failed=True,
        )
        self.states.alert(level=level, message=message)

    _aler = alert

    def pattern(self, pattern: str) -> Any:
        token = self.cursor.matchre(pattern)
        if token is None:
            self.tracer.trace_match(self.cursor, '', pattern, failed=True)
            raise self.newexcept(f'Expecting {regexpp(pattern)}', excls=FailedPattern)
        self.tracer.trace_match(self.cursor, token, pattern)
        self.state.append(token)
        return token

    _pattern = pattern

    def eof(self) -> bool:
        return self.cursor.atend()

    def eol(self) -> bool:
        return self.cursor.ateol()

    def eofcheck(self) -> None:
        self.next_token()
        if not self.cursor.atend():
            raise self.newexcept(
                'Expecting end of text',
                excls=FailedExpectingEndOfText,
            )

    _check_eof = eofcheck

    @contextmanager
    def _try(self) -> Any:
        self.pushstate()
        try:
            yield
            self.mergestate()
        except FailedParse:
            self.undostate()
            raise

    def _no_more_options(self) -> bool:
        # NOTE:
        #  In previous versiions, used by the Python code generator
        #  so there are no unconditional:
        #  `
        #      raise self.newexception(...)
        #  `
        #  that fool the syntax highlighting of editors
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

    _option = option

    @contextmanager
    def choice(self) -> Generator[ChoiceContext, Any, Any]:
        chc = ChoiceContext(self)
        with suppress(OptionSucceeded), self.states.cutscope():
            yield chc
            chc.run()

    _choice = choice

    @contextmanager
    def optional(self) -> Any:
        with self._choice(), self._option(), self.states.cutscope():
            yield

    _optional = optional

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

    _group = group

    @contextmanager
    def if_(self) -> Any:
        self.pushstate()
        self.lookahead += 1
        try:
            yield
        finally:
            self.undostate()
            self.lookahead -= 1

    _if = if_

    @contextmanager
    def ifnot_(self) -> Any:
        try:
            with self.if_():
                yield
        except ParseException:
            pass
        else:
            raise self.newexcept('', excls=FailedLookahead)

    _ifnot = ifnot_

    @contextmanager
    def nameset(self, name: str) -> Any:
        yield
        self.setname(name)

    _setname = nameset

    @contextmanager
    def nameadd(self, name: str) -> Any:
        yield
        self.addname(name)

    _addname = nameadd

    def _isolate(self, exp: Func, _drop: bool = False) -> Any:
        self.pushstate()
        try:
            exp(self)
            return listclosure(self.cst) if is_list(self.cst) else self.cst
        finally:
            ast = self.ast
            self.popstate()
            self.ast = ast

    def _repeat(
        self,
        exp: Func,
        prefix: Func | None = None,
        dropprefix: bool = False,
    ) -> None:
        while True:
            with self._choice():
                with self._option():
                    p = self.pos

                    if prefix:
                        pcst = self._isolate(prefix, _drop=dropprefix)
                        if not dropprefix:
                            self.state.append(pcst)
                        self.cut()

                    cst = self._isolate(exp)
                    self.state.append(cst)

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

    def closure(
        self,
        exp: Func,
        sep: Func | None = None,
        omitsep: bool = False,
    ) -> Any:
        self.pushstate()
        try:
            self.cst = []
            with self.states.cutscope():
                with self._optional():
                    exp(self)
                    self.cst = [self.cst]
                self._repeat(exp, prefix=sep, dropprefix=omitsep)
            self.cst = cst =listclosure(self.cst)
            self.mergestate()
            return cst
        except ParseException:
            self.undostate()
            raise

    _closure = closure

    def positive_closure(
        self,
        exp: Func,
        sep: Func | None = None,
        omitsep: bool = False,
    ) -> Any:
        self.pushstate()
        try:
            with self.states.cutscope():
                exp(self)
                self.cst = [self.cst]
                self._repeat(exp, prefix=sep, dropprefix=omitsep)
            self.cst = cst =listclosure(self.cst)
            self.mergestate()
            return cst
        except ParseException:
            self.undostate()
            raise

    _positive_closure = positive_closure

    def empty(self) -> list:
        cst = listclosure([])
        self.state.append(cst)
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

    def gather(self, exp: Func, sep: Func) -> Any:
        return self._closure(exp, sep=sep, omitsep=True)

    _gather = gather

    def positive_gather(self, exp: Func, sep: Func) -> Any:
        return self._positive_closure(exp, sep=sep, omitsep=True)

    _positive_gather = positive_gather

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

    def join(self, exp: Func, sep: Func) -> Any:
        return self._closure(exp, sep=sep)

    _join = join

    def positive_join(self, exp: Func, sep: Func) -> Any:
        return self._positive_closure(exp, sep=sep)

    _positive_join = positive_join

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

    def left_join(self, exp: Func, sep: Func) -> Any:
        self.cst = left_assoc(self._positive_join(exp, sep))
        return self.cst

    _left_join = left_join

    def right_join(self, exp: Func, sep: Func) -> Any:
        self.cst = right_assoc(self._positive_join(exp, sep))
        return self.cst

    _right_join = right_join

    def void(self) -> Any:
        self.next_token()
        return ()

    _void = void

    def dot(self) -> Any:
        c = self._next()
        if c is None:
            self.tracer.trace_match(self.cursor, c, failed=True)
            raise self.newexcept(c, excls=FailedToken) from None
        self.tracer.trace_match(self.cursor, c)
        self.state.append(c)
        return c

    _dot = dot

    @contextmanager
    def skipto(self) -> Any:
        cl = InnerExpContext(self)
        yield cl
        self.skip_to(cl._exp_value())

    _skipto = skipto

    def skip_to(self, exp: Func) -> Any:
        while not self.eof():
            try:
                with self.if_():
                    exp(self)
            except FailedParse:
                pass
            else:
                break
            pos = self.pos
            self.next_token()
            if self.pos == pos:
                self._next()
        return exp(self)

    _skip_to = skip_to
