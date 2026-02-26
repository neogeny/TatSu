# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from ..infos import RuleInfo
from ..protocol import ParseCtx


def tatsumasu(
    *params: Any, **kwparams: Any
) -> Callable[Callable[[], None], Callable[[ParseCtx], Any]]:
    def decorator(func: Callable[[], None]) -> Callable[[ParseCtx], Any]:
        @functools.wraps(func)
        def wrapper(self: ParseCtx, _ctx: ParseCtx | None = None) -> Any:
            ruleinfo = RuleInfo.new(self, func, params, kwparams)
            return self._call(ruleinfo)

        return wrapper

    return decorator  # pyright: ignore[reportReturnType]
