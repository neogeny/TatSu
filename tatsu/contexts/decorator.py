# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, cast

from .protocol import ParseCtx

from .infos import RuleInfo, RuleLike
from ..util import debug  # noqa


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


def fn(func: Callable) -> str:
    return getattr(func, '__name__', '<?>')

def tn(obj: Any) -> str:
    return getattr(type(obj), '__name__', '.?.')


# note: decorator
class rule:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if func := kwargs.pop('func', None):
            self.func = func
        else:
            self.func = None
        # debug(f'__init__ {fn(self.func)!r} {args=!r} {kwargs=!r}')
        self.obj = None
        self.params = args
        self.kwparams = kwargs
        self.owner = None

    def __get__(self, instance: Any, owner: Any = None) -> Any:
        self.obj = instance

        debug(
            f'__get__ {fn(self.func)=!r} {instance=!r} {owner=!r}'
            f'  {tn(self.obj)=!r} '
        )
        if issubclass(owner, ParseCtx) and isinstance(instance, ParseCtx):
            debug(f'__get__ LEGACY {instance=!r} {owner=!r}')
            @functools.wraps(self.func)
            def wrapper(_ctx: Any = None) -> Any:
                debug(
                    f'__legacy_wrapper__@__get__' 
                    f' {fn(self.func)!r} {_ctx=!r} {instance=!r} {fn(owner)=!r}'
                )
                assert isinstance(instance, ParseCtx)
                ruleinfo = RuleInfo.new(instance, self.func, self.params, self.kwparams)
                return instance._call(ruleinfo)

            return wrapper

        @functools.wraps(self.func)
        def wrapper(ctx: ParseCtx) -> Any:
            debug(
                f'__wrapper__@__get__ {fn(self.func)!r} {instance=!r} {tn(ctx)=!r}' 
                f' {fn(instance)=!r} {fn(owner)!r}'
            )
            ruleinfo = RuleInfo.new(self.obj, self.func, self.params, self.kwparams)
            assert isinstance(ctx, ParseCtx)
            return ctx._call(ruleinfo)

        return wrapper

    def __call__(self, *args, **kwargs) -> Any:
        # debug(f'__call__ {self.obj=} {args=} {kwargs=}')
        func = args[0] if args else None
        if not self.func:
            self.func = func
        if not self.obj:
            other = rule(*self.params, func=func, **self.kwparams)
            other.func = func
            return other

        @functools.wraps(func)
        def wrapper(ctx: ParseCtx | None = None) -> Any:
            ruleinfo = RuleInfo.new(self.obj, func, self.params, self.kwparams)
            # debug(f'__wrapper__@__call__ {tn(self.obj)=!r} {fn(ctx)=!r} {ruleinfo=!r}')
            if isinstance(ctx, ParseCtx):
                return ctx._call(ruleinfo)
            else:
                # note: methods for rules used to be declared in the parser object
                return obj._call(ruleinfo)

        return wrapper
