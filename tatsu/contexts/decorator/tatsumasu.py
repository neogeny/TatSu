# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from ..infos import RuleInfo
from ..protocol import Ctx


def tatsumasu(
    *params: Any, **kwparams: Any
) -> Callable[Callable[[], None], Callable[[Ctx], Any]]:
    def decorator(func: Callable[[], None]) -> Callable[[Ctx], Any]:
        @functools.wraps(func)
        def wrapper(self: Ctx, _ctx: Ctx | None = None) -> Any:
            ruleinfo = RuleInfo.new(self, func, params, kwparams)
            return self._call(ruleinfo)

        return wrapper

    return decorator  # pyright: ignore[reportReturnType]
