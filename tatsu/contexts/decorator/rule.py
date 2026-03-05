# ruff: noqa: F811
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, cast, overload

from ..infos import RuleInfo
from ..protocol import Ctx


def __rule_wrapper(func: Callable, *args: Any, **kwargs: Any) -> Callable:
    ribase = RuleInfo.new(None, func, args, kwargs)

    @functools.wraps(func)
    def wrapper(instance: Any, ctx: Ctx) -> Any:
        ri = RuleInfo.bind(ribase, instance)
        return ctx.call(ri)

    return wrapper


def rule(*args: Any, **kwargs: Any) -> Callable:
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func: Callable = cast(Callable, args[0])
        return __rule_wrapper(func)

    def decorator(func: Callable) -> Callable[[Any, Ctx], Any]:
        return __rule_wrapper(func, *args, *kwargs)

    return decorator
