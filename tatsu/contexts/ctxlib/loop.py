# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ...exceptions import ParseException
from .._protocol import Ctx, Func
from ..cst import closedlist
from .exp import ExpContext


class LoopContext(ExpContext):
    def __init__(self, ctx: Ctx, plus: bool = False):
        super().__init__(ctx)
        self.plus = plus

    def _inner_iter(self, ctx: Ctx, func: Func) -> Iterator[Any]:
        yield ctx.isolate(func)

    def parse(self, ctx: Ctx) -> Any:
        if self.plus:
            return ctx.positive_closure(self.func)
        else:
            return ctx.closure(self.func)
