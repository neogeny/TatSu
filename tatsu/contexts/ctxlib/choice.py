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

    def parse(self, ctx: Ctx) -> Any:
        if not self.options:
            return None
        for opt in self.options:
            with ctx.option():
                return opt(ctx)
        raise self.expectedexcept(ctx)
