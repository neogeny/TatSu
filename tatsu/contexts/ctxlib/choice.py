# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..protocol import Ctx


class ChoiceContext:
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.options: list[Callable[[], Any]] = []
        self.expected: list[str] = []

    def option(self, func: Callable[[], Any]) -> Callable[[], None]:
        self.options.append(func)
        return func

    def expecting(self, *tokens: str) -> None:
        self.expected.extend(tokens)

    def run(self) -> None:
        if not self.options:
            return
        for opt in self.options:
            with self.ctx.option():
                opt()
        raise self.ctx.newexcept(f"Expected one of: {', '.join(self.expected)}")
