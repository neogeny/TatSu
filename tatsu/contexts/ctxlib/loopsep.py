# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._protocol import Ctx, Func
from ..cst import closedlist
from .loop import LoopContext


class LoopWithSepContext(LoopContext):
    def __init__(self, withsep: bool = False):
        super().__init__()
        self.withsep = withsep
        self._sep: Func | None = None

    @property
    def sep_func(self) -> Func:
        if self._sep is None:
            raise RuntimeError('.sep not set')
        return self._sep

    def sep(self, func: Func) -> Func:
        if self._sep is not None:
            raise RuntimeError('.sep already set')
        self._sep = func
        return func

    def parse(self, ctx: Ctx) -> Any:
        def iter(func) -> Iterator[Any]:
            with ctx.optional():
                sep = ctx.isolate(self.sep_func)
                if self.withsep:
                    yield sep
                yield ctx.isolate(func)
                yield from iter(func)

        with ctx.optional():
            cst = ctx.isolate(super().func)
            return closedlist([cst, *iter(super().func)])
