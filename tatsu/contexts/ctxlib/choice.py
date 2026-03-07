# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .._protocol import Ctx


class ChoiceContext:
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.options: list[Callable[[Ctx], Any]] = []
        self.expected: list[str] = []
        self.result: Any = None

    def option(self, func: Callable[[Ctx], Any]) -> Callable[[Ctx], None]:
        self.options.append(func)
        return func

    def expecting(self, *tokens: str) -> None:
        self.expected.extend(tokens)

    def run(self) -> Any:
        if not self.options:
            return
        for opt in self.options:
            with self.ctx.option():
                self.result = opt(self.ctx)
        raise self.ctx.newexcept(f"Expected one of: {' '.join(self.expected)}")
