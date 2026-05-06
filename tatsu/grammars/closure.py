#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from functools import cached_property
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import indent
from .math import ffset, kdot
from .model import Box, Func, Model


@nodedataclass
class Closure(Box):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.closure(self.exp._parse)

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

    @cached_property
    def _nullable(self) -> bool:
        return True

    def optimized(self) -> Model:
        from .syntax import Group

        exp = self.exp.optimized()
        if isinstance(exp, Group):
            exp = exp.exp
        return self.clone(exp=exp)  # pyright: ignore[reportArgumentType]


@nodedataclass
class PositiveClosure(Closure):
    def _parse(self, ctx: Ctx) -> Any:
        parse: Func = self.exp._parse  # type: ignore
        return ctx.positive_closure(parse)

    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    @cached_property
    def _nullable(self) -> bool:
        return self.exp.is_nullable()


@nodedataclass
class Join(Box):
    JOINOP = '%'

    sep: Model = Model()

    def __post_init__(self):
        super().__post_init__()
        assert not self.ast or self.sep == self.ast.sep, self.sep

    def _parse(self, ctx: Ctx) -> Any:
        return self._do_parse(ctx, self.exp._parse, self.sep._parse)

    def _do_parse(self, ctx: Ctx, exp: Func, sep: Func) -> Any:
        return ctx.join(exp, sep)

    def _pretty(self, lean=False):
        ssep = self.sep._pretty(lean=lean)
        sexp = str(self.exp._pretty(lean=lean))
        if len(sexp.splitlines()) <= 1:
            return f'{ssep}{self.JOINOP}{{{sexp}}}'
        else:
            return f'{ssep}{self.JOINOP}{{\n{sexp}\n}}'

    @cached_property
    def _nullable(self) -> bool:
        return True

    def optimized(self) -> Model:
        from .syntax import Group

        exp = self.exp.optimized()
        if isinstance(exp, Group):
            exp = exp.exp
        return self.clone(exp=exp)  # pyright: ignore[reportArgumentType]


class PositiveJoin(Join):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        return ctx.positive_join(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    @cached_property
    def _nullable(self) -> bool:
        return self.exp._nullable


class Gather(Join):
    JOINOP = '.'

    def _do_parse(self, ctx, exp, sep):
        return ctx.gather(exp, sep)


class PositiveGather(Gather):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        return ctx.positive_gather(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    @cached_property
    def _nullable(self) -> bool:
        return self.exp.is_nullable()


@nodedataclass
class EmptyClosure(Model):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.empty()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '{}'

    @cached_property
    def _nullable(self) -> bool:
        return True
