# ruff: noqa: F811
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from copy import copy
from typing import Any
from collections.abc import Callable

from ...util import debug  # noqa: PGH004
from ..engine import ParseContext
from ..protocol import ParseCtx
from ..infos import RuleInfo


def _debug(*_args, **_kwargs) -> None:  # noqa: F811
    pass


def fn(func) -> str:
    return getattr(func, '__name__', '<?>')


def tn(obj) -> str:
    return getattr(type(obj), '__name__', '.?.')


class rule:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # note: we may be new instance created by self.__call__()
        self.func: Callable[..., Any] | None = kwargs.pop('func', None)
        debug(f'__init__ {id(self)=} {fn(self.func)!r} {args=!r} {kwargs=!r}')
        self.params = args
        self.kwparams = kwargs

    def __call__(self, func: Callable) -> Any:
        debug(f'__call__ {id(self)=} {fn(func)=}')
        assert isinstance(func, Callable)
        return rule(*self.params, func=func, **self.kwparams)

    def __get__(self, instance: Any, owner: Any = None) -> Any:
        debug(
            f'__get__ {id(self)=}'
            f' { fn(self.func)=!r} {instance=!r} {owner=!r}'
            f'  {tn(instance)=!r}'
            f'  {self.params=!r} {self.kwparams=!r}'
        )
        owner = owner or type(instance)
        func = self.func
        params = copy(self.params) or ()
        kwparams = copy(self.kwparams) or {}
        assert isinstance(func, Callable)

        if issubclass(owner, ParseContext) and isinstance(instance, ParseCtx):
            # NOTE:
            #  v5.16 <= parser <= v5.17.1 may use @rule on methods
            #  defined inside a ParseContext
            debug(f'__get__ LEGACY {instance=!r} {owner=!r}')

            assert isinstance(func, Callable)
            @functools.wraps(func)
            def transition_wrapper(_ctx: Any = None) -> Any:
                debug(
                    f'__transition_wrapper__@__get__'
                    f' {fn(func)!r} {_ctx=!r} {instance=!r} {fn(owner)=!r}'
                    f' {params=!r} {kwparams=!r}'
                )
                assert isinstance(instance, ParseContext)
                assert isinstance(func, Callable)
                ruleinfo = RuleInfo.new(instance, func, params, kwparams)
                return instance._call(ruleinfo)

            return transition_wrapper

        @functools.wraps(self.func)
        def wrapper(ctx: ParseCtx) -> Any:
            debug(
                f'__wrapper__@__get__ {id(self)=} {fn(func)!r} {
                instance=!r} { tn(ctx)=!r}'
                f' {fn(instance)=!r} {fn(owner)!r}'
                f' {params=!r} {kwparams=!r}'
            )
            assert isinstance(func, Callable)
            assert isinstance(ctx, ParseContext)
            ruleinfo = RuleInfo.new(instance, func, params, kwparams)
            return ctx._call(ruleinfo)

        return wrapper
