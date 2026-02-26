# ruff: noqa: F811
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from typing import Any
from collections.abc import Callable

from ...util import debug  # noqa: PGH004
from ..engine import ParseContext
from ..protocol import ParseCtx
from ..infos import RuleInfo


def debug(*_args, **_kwargs) -> None:  # noqa: F811
    pass


def fn(func) -> str:
    return getattr(func, '__name__', '<?>')


def tn(obj) -> str:
    return getattr(type(obj), '__name__', '.?.')


class rule:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # note: we may be an instance created by self
        self.func: Callable[..., Any] | None = kwargs.pop('func', None)
        debug(f'__init__ {fn(self.func)!r} {args=!r} {kwargs=!r}')
        self.obj = None
        self.params = args
        self.kwparams = kwargs
        self.owner = None

    def __get__(self, instance: Any, owner: Any = None) -> Any:
        self.obj = instance

        debug(
            f'__get__ { fn(self.func)=!r} {instance=!r} {owner=!r}'
            f'  { tn(self.obj)=!r} '
        )
        owner = owner or type(instance)
        if issubclass(owner, ParseContext) and isinstance(instance, ParseCtx):
            # NOTE:
            #  v5.16 <= parser <= v5.17.1
            #  may use @rule on methods defined inside MyParser
            debug(f'__get__ LEGACY {instance=!r} {owner=!r}')
            assert isinstance(self.func, Callable)

            @functools.wraps(self.func)
            def transition_wrapper(_ctx: Any = None) -> Any:
                debug(
                    f'__transition_wrapper__@__get__'
                    f' {fn(self.func)!r} {_ctx=!r} {instance=!r} {fn(owner)=!r}'
                )
                assert isinstance(instance, ParseContext)
                assert isinstance(self.func, Callable)
                ruleinfo = RuleInfo.new(instance, self.func, self.params, self.kwparams)
                return instance._call(ruleinfo)
            return transition_wrapper

        assert isinstance(self.func, Callable)

        @functools.wraps(self.func)
        def wrapper(ctx: ParseCtx) -> Any:
            debug(
                f'__wrapper__@__get__ {fn(self.func)!r} {instance=!r} { tn(ctx)=!r}'
                f' { fn(instance)=!r} {fn(owner)!r}'
            )
            assert isinstance(self.func, Callable)
            assert isinstance(ctx, ParseContext)
            ruleinfo = RuleInfo.new(self.obj, self.func, self.params, self.kwparams)
            return ctx._call(ruleinfo)
        return wrapper

    def __call__(self, *args, **kwargs) -> Any:
        debug(f'__call__ {self.obj=} {args=} {kwargs=}')
        func: Callable[..., Any] | None = args[0] if args else None
        if not self.func:
            self.func = func
        if not self.obj:
            other = rule(*self.params, func=func, **self.kwparams)
            other.func = func
            return other

        assert isinstance(self.func, Callable)

        @functools.wraps(self.func)
        def wrapper(ctx: ParseCtx | None = None) -> Any:
            assert isinstance(self.func, Callable)
            ctx = ctx or self.obj
            ruleinfo = RuleInfo.new(self.obj, self.func, self.params, self.kwparams)
            debug(f'__wrapper__@__call__ {tn(self.obj)=!r} {fn(ctx)=!r} {ruleinfo=!r}')
            assert isinstance(ctx, ParseContext)
            return ctx._call(ruleinfo)

        return wrapper
