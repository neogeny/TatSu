# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, cast

from .engine import ParseContext
from .infos import RuleInfo, RuleLike


def leftrec(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_leftrec = True
    over.is_memoizable = False
    return impl


def nomemo(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_memoizable = False
    return impl


def isname(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_name = True

    return impl


type RuleFunc = Callable[[Any, Any | None], None]
# type RuleFunc = Callable[..., Any]

type DecoratedRuleFunc = Callable[[ParseContext, Any], Any]


def rule(
    *params: Any,
    **kwparams: Any,
) -> Callable[[RuleFunc], DecoratedRuleFunc]:

    def decorator(impl: RuleFunc) -> DecoratedRuleFunc:
        @functools.wraps(impl)
        def wrapper(ctx: ParseContext, ss: Any) -> Any:
            name = impl.__name__  # type: ignore
            # remove the single leading and trailing underscore
            # that the parser generator added
            if name.startswith("_") and name.endswith("_"):
                name = name[1:-1]
            is_leftrec = getattr(impl, 'is_leftrec', False)
            is_memoizable = getattr(impl, 'is_memoizable', True)
            is_name = getattr(impl, 'is_name', False)
            ruleinfo = RuleInfo(
                name,
                impl,
                is_leftrec,
                is_memoizable,
                is_name,
                params,
                kwparams,
            )
            self = ctx
            return self._call(ss, ruleinfo)

        return wrapper

    return decorator
