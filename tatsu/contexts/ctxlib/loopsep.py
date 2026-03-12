# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._protocol import Ctx, Func
from ..cst import closedlist
from .loop import LoopContext


class LoopWithSepContext(LoopContext):
    def __init__(self, ctx: Ctx, plus=True, omitsep: bool = True):
        super().__init__(ctx, plus=plus)
        self.omitsep = omitsep
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

    def _inner_iter(self, ctx: Ctx, func: Func) -> Iterator[Any]:
        sep = ctx.isolate(self.sep_func)
        if not self.omitsep:
            yield sep
        yield ctx.isolate(func)

    def parse(self, ctx: Ctx) -> Any:
        if self.plus:
            return ctx.positive_closure(self.func, sep=self.sep_func, omitsep=self.omitsep)
        else:
            return ctx.closure(self.func, sep=self.sep_func, omitsep=self.omitsep)
