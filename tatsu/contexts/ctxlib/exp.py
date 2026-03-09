# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .._protocol import Ctx, Func


class InnerExpContext:
    def __init__(self, ctx: Ctx, nosep: bool = False):
        self.ctx = ctx
        self._nosep = nosep
        self._exp: Func | None = None
        self._sep: Func | None = None

    def _exp_value(self) -> Func:
        if self._exp is None:
            raise RuntimeError('.exp not set')
        return self._exp

    def _sep_value(self) -> Func:
        if self._sep is None:
            raise RuntimeError('.sep not set')
        return self._sep

    def exp(self, func: Func) -> Func:
        if self._exp is not None:
            raise RuntimeError('.exp already set')
        self._exp = func
        return func

    def sep(self, func: Func) -> Func:
        if self._sep is not None:
            raise RuntimeError('.sep already set')
        if self._nosep:
            raise RuntimeError('.sep nor available')
        self._sep = func
        return func
