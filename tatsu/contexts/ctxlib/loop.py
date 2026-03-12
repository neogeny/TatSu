# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._protocol import Ctx, Func
from ..cst import closedlist
from .exp import ExpContext


class LoopContext(ExpContext):
    def __init__(self, ctx: Ctx):
        super().__init__(ctx)

    @property
    def func(self) -> Func:
        return self.iterate

    def iterate(self, ctx: Ctx) -> Any:
        def iter(func) -> Iterator[Any]:
            with ctx.optional():
                yield ctx.isolate(func)
                yield from iter(func)

        return closedlist(iter(super().func))
