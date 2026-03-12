# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from types import TracebackType
from typing import Any

from .._protocol import Ctx, Func


class ContextBase:
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.expected: list[str] = []

    def expecting(self, *tokens: str) -> None:
        self.expected.extend(tokens)

    def expectedexcept(self, ctx: Ctx) -> Exception:
        msg = 'Failed'
        if self.expected:
            msg = f'Expected one of: {' '.join(self.expected)}'
        return ctx.newexcept(msg)

    def parse(self, ctx: Ctx) -> Any:
        return None

    def __enter__(self) -> ContextBase:
        return self

    def __exit__(
        self,
        etype: type[BaseException] | None,
        evalue: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        # If an exception occurred inside the 'with' block,
        # returning False re-raises it automatically.
        if etype is not None:
            return False

        # If no exception, execute the parsing logic
        self.parse(self.ctx)
        return True
