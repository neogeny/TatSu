#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..contexts import Ctx, ParseContext
from ..objectmodel import nodedataclass
from ..util import cast, indent
from ._core import Func, Model
from .math import ffset, kdot
from .syntax import Box


@nodedataclass
class Closure(Box):
    def _parse(self, ctx: Ctx) -> Any:
        ctx = cast(ParseContext, ctx)
        parse: Callable[[Ctx], Any] = self.exp._parse  # type: ignore
        return ctx._closure(parse)

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


@nodedataclass
class PositiveClosure(Closure):
    def _parse(self, ctx: Ctx) -> Any:
        ctx = cast(ParseContext, ctx)
        parse: Callable[[Ctx], Any] = self.exp._parse  # type: ignore
        return ctx._positive_closure(parse)

    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


@nodedataclass
class Join(Box):
    JOINOP = '%'

    sep: Model = Model()

    def __post_init__(self):
        super().__post_init__()
        assert self.sep == self.ast.sep, self.sep

    def _parse(self, ctx: Ctx) -> Any:
        return self._do_parse(ctx, self.exp._parse, self.sep._parse)

    def _do_parse(self, ctx: Ctx, exp: Func, sep: Func) -> Any:
        ctx = cast(ParseContext, ctx)
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
        ctx = cast(ParseContext, ctx)
        return ctx._positive_join(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


class LeftJoin(PositiveJoin):
    JOINOP = '<'

    def _do_parse(self, ctx, exp, sep):
        ctx = cast(ParseContext, ctx)
        return ctx._left_join(exp, sep)


class RightJoin(PositiveJoin):
    JOINOP = '>'

    def _do_parse(self, ctx, exp, sep):
        ctx = cast(ParseContext, ctx)
        return ctx._right_join(exp, sep)


class Gather(Join):
    JOINOP = '.'

    def _do_parse(self, ctx, exp, sep):
        ctx = cast(ParseContext, ctx)
        return ctx._gather(exp, sep)


class PositiveGather(Gather):
    def _first(self, k, f) -> ffset:
        return self.exp._first(k, f)

    def _do_parse(self, ctx, exp, sep):
        ctx = cast(ParseContext, ctx)
        return ctx._positive_gather(exp, sep)

    def _pretty(self, lean=False):
        return super()._pretty(lean=lean) + '+'

    def _nullable(self) -> bool:
        return self.exp._nullable()


@nodedataclass
class EmptyClosure(Model):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.empty()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '{}'

    def _nullable(self) -> bool:
        return True
