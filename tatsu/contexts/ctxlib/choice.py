# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .._protocol import Ctx, Func
from ._base import ContextBase


class ChoiceContext(ContextBase):
    def __init__(self, ctx: Ctx):
        super().__init__(ctx)
        self.options: list[Func] = []
        self.result: Any = None

    def option(self, func: Func) -> Func:
        self.options.append(func)
        return func

    def run(self) -> Any:
        if not self.options:
            return
        for opt in self.options:
            with self.ctx.option():
                self.result = opt(self.ctx)
        raise self.expectedexcept()
