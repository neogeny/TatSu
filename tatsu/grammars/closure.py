# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..objectmodel import tatsudataclass
from ..util import indent
from ._core import Model
from .math import ffset, kdot
from .syntax import Decorator


@tatsudataclass
class Closure(Decorator):
    def _parse(self, ctx):
        return ctx._closure(lambda: self.exp._parse(ctx))

    def _first(self, k, f) -> ffset:
        efirst = self.exp._first(k, f)
        result: ffset = {()}
        for _i in range(k):
            result = kdot(result, efirst, k)
        return {()} | result

    def _pretty(self, lean=False):
        sexp = str(self.exp._pretty(lean=lean))
        if len(sexp.splitlines()) <= 1:
            return f'{{{sexp}}}'
        else:
            return f'{{\n{indent(sexp)}\n}}'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class PositiveClosure(Closure):
    def _parse(self, ctx):
        return ctx._positive_closure(lambda: self.exp._parse(ctx))

    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


@tatsudataclass
class Join(Decorator):
    JOINOP = '%'

    sep: Model = Model()

    def __post_init__(self):
        super().__post_init__()
        assert self.sep == self.ast.sep, self.sep

    def _parse(self, ctx):
        def sep():
            return self.sep._parse(ctx)

        def exp():
            return self.exp._parse(ctx)

        return self._do_parse(ctx, exp, sep)

    def _do_parse(self, ctx, exp, sep):
        return ctx._join(exp, sep)

    def _pretty(self, lean=False):
        ssep = self.sep._pretty(lean=lean)
        sexp = str(self.exp._pretty(lean=lean))
        if len(sexp.splitlines()) <= 1:
            return f'{ssep}{self.JOINOP}{{{sexp}}}'
        else:
            return f'{ssep}{self.JOINOP}{{\n{sexp}\n}}'

    def _nullable(self) -> bool:
        return True


class PositiveJoin(Join):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        return ctx._positive_join(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


class LeftJoin(PositiveJoin):
    JOINOP = '<'

    def _do_parse(self, ctx, exp, sep):
        return ctx._left_join(exp, sep)


class RightJoin(PositiveJoin):
    JOINOP = '>'

    def _do_parse(self, ctx, exp, sep):
        return ctx._right_join(exp, sep)


class Gather(Join):
    JOINOP = '.'

    def _do_parse(self, ctx, exp, sep):
        return ctx._gather(exp, sep)


class PositiveGather(Gather):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        return ctx._positive_gather(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


@tatsudataclass
class EmptyClosure(Model):
    def _parse(self, ctx):
        return ctx._empty_closure()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '{}'

    def _nullable(self) -> bool:
        return True
