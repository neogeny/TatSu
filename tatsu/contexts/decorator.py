# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, cast

from .protocol import ParseCtx

from .infos import RuleInfo, RuleLike
from ..util import debug


# note: decorator
def leftrec(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_leftrec = True
    over.is_memoizable = False
    return impl


# note: decorator
def nomemo(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_memoizable = False
    return impl


# note: decorator
def isname(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_name = True
    return impl


# note: decorator
def name(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_name = True
    return impl


# note: decorator
class rule:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # allways used as rule()
        if not __debug__:
            raise RuntimeError('WANT DEBUG')
        debug(f'__init__ {args=!r} {kwargs=!r}')
        self.obj = None
        self.func = None
        self.params = args
        self.kwparams = kwargs
        self.owner = None

    def __get__(self, obj: Any, owner: Any = None) -> Any:
        debug(f'__get__ {obj=!r} {owner=!r}')
        self.obj = owner or obj
        return self

    def __call__(self, func: Callable) -> Any:
        debug(f'__call__ {self.obj=} {func=}')
        self.func = func

        @functools.wraps(func)
        def wrapper(obj: Any, ctx: ParseCtx | None = None) -> Any:
            ruleinfo = RuleInfo.new(obj, func, self.params, self.kwparams)
            debug(f'__wrapper__ {obj=!r} {ctx=!r} {ruleinfo=!r}')
            if isinstance(ctx, ParseCtx):
                return ctx._call(ruleinfo)

            # note:
            #   methods for rules used to be declared in the parser object
            return obj._call(ruleinfo)  # legacy case

        return wrapper
