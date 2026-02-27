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
from ..protocol import Ctx
from ..infos import RuleInfo


def debug(*_args, **_kwargs) -> None:  # noqa: F811
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

    def __call__(self, *args, **kwargs) -> Any:
        debug(f'__call__ {id(self)=} {args=!r} {kwargs=!r}')
        func = args[0] if args else None
        if callable(func):
            return rule(*self.params, func=func, **self.kwparams)
        else:
            # note: this self may be being reused
            return rule(*args, **kwargs)

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

        ruleinfo = RuleInfo.new(instance, func, params, kwparams)
        if issubclass(owner, ParseContext) and isinstance(instance, Ctx):
            # NOTE:
            #  v5.16 <= parser <= v5.17.1 may use @rule on methods
            #  defined inside a ParseContext
            debug(f'__get__ LEGACY {instance=!r} {owner=!r}')
            return self._rules_in_ctx(id(self), ruleinfo)
        else:
            return self._rules_in_obj(id(self), ruleinfo)

    @staticmethod
    def _rules_in_obj(selfid, ruleinfo: RuleInfo) -> Any:
        @functools.wraps(ruleinfo.func)
        def wrapper(ctx: Ctx) -> Any:
            ri = ruleinfo
            debug(
                f'__wrapper__@__get__ {selfid=} {fn(ri.func)!r}'
                f' {tn(ri.instance)=!r} { tn(ctx)=!r}'
                f' {ri.params=!r} {ri.kwparams=!r}'
            )
            assert isinstance(ri.func, Callable)
            assert isinstance(ctx, Ctx)
            return ctx._call(ruleinfo)

        return wrapper

    @staticmethod
    def _rules_in_ctx(selfid, ruleinfo: RuleInfo) -> Any:
        ri = ruleinfo
        assert isinstance(ri.func, Callable)

        @functools.wraps(ri.func)
        def transition_wrapper(_ctx: Any = None) -> Any:
            debug(
                f'__rules_in_ctx_wrapper__@__get__ {selfid=}'
                f' {fn(ri.func)!r} {_ctx=!r} {ri.instance=!r}'
                f' {ri.params=!r} {ri.kwparams=!r}'
            )
            assert isinstance(ri.instance, ParseContext)
            assert isinstance(ri.func, Callable)
            return ri.instance._call(ruleinfo)

        return transition_wrapper
