# ruff: noqa: F811
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from copy import copy
from typing import Any
from collections.abc import Callable

from twine.cli import args

from ...util import debug  # noqa: PGH004
from ..engine import ParseContext
from ..protocol import Ctx
from ..infos import RuleInfo


def _debug(*_args, **_kwargs) -> None:  # noqa: F811
    pass


def fn(func) -> str:
    return getattr(func, '__name__', '<?>')


def tn(obj) -> str:
    return getattr(type(obj), '__name__', '.?.')


def __rule_wrapper(func: Callable[[Any, Ctx], Any], params, kwparams) -> Callable[[Any, Ctx], Any]:
    @functools.wraps(func)
    def wrapper(self: Any, ctx: Ctx) -> Any:
        ruleinfo = RuleInfo.new(self, func, params, kwparams)
        return ctx._call(ruleinfo)

    return wrapper


def rule(
    *args: Any, **kwargs: Any
) ->  Callable[[Callable[[Any, Ctx], None]], Callable[[Any, Ctx], Any]]:

    if len(args) == 1 and callable(args[0]) and not kwargs:
        func: Callable[[Any, Ctx], None] = args[0]
        return __rule_wrapper(func, (), {})

    def decorator(func: Callable[[Any, Ctx], None]) -> Callable[[Any, Ctx], Any]:
        return __rule_wrapper(func, args, kwargs)

    return decorator
