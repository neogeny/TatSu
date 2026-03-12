# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .._protocol import Ctx, Func
from .exp import ExpContext


class ExpWithSepContext(ExpContext):
    def __init__(self, ctx: Ctx):
        super().__init__()
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
