# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .._protocol import Ctx, Func
from ._base import ContextBase


class ExpContext(ContextBase):
    def __init__(self, ctx: Ctx):
        super().__init__(ctx)
        self._exp: Func | None = None

    @property
    def func(self) -> Func:
        if self._exp is None:
            raise RuntimeError('.exp not set')
        return self._exp

    def exp(self, func: Func) -> Func:
        if self._exp is not None:
            raise RuntimeError('.exp already set')
        self._exp = func
        return func
