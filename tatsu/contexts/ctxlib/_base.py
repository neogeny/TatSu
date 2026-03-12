# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .._protocol import Ctx, Func


class ContextBase:
    def __init__(self):
        self.expected: list[str] = []

    def expecting(self, *tokens: str) -> None:
        self.expected.extend(tokens)

    def expectedexcept(self, ctx: Ctx) -> Exception:
        if self.expected:
            return ctx.newexcept(f"Expected one of: {' '.join(self.expected)}")
        return ctx.newexcept('Failed')
