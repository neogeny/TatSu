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
from .tatsumasu import tatsumasu


def debug(*_args, **_kwargs) -> None:  # noqa: F811
    pass


def fn(func) -> str:
    return getattr(func, '__name__', '<?>')


def tn(obj) -> str:
    return getattr(type(obj), '__name__', '.?.')


class rule:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.func: Callable[..., Any] | None = None
        if func := kwargs.pop('func', None):
            self.func = func
        # debug(f'__init__ {fn(self.func)!r} {args=!r} {kwargs=!r}')
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
            # WARNING:
            #  v5.15 <= parsers <= v5.17.1  may use @rule on methods defined in Parser
            debug(f'__get__ LEGACY {instance=!r} {owner=!r}')
            # note: return the legacy wrapper
            return tatsumasu(*self.params, **self.kwparams)(self.func) # pyright: ignore[reportCallIssue]

        assert isinstance(self.func, Callable)

        @functools.wraps(self.func)
        def wrapper(ctx: ParseCtx) -> Any:
            debug(
                f'__wrapper__@__get__ {fn(self.func)!r} {instance=!r} { tn(ctx)=!r}'
                f' { fn(instance)=!r} {fn(owner)!r}'
            )
            assert isinstance(self.func, Callable)
            ruleinfo = RuleInfo.new(self.obj, self.func, self.params, self.kwparams)
            assert isinstance(ctx, ParseCtx)
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
            assert isinstance(ctx, ParseCtx)
            return ctx._call(ruleinfo)

        return wrapper
