# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, cast

from tatsu.contexts.engine import ParseContext

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


def name(impl: Callable) -> Callable:
    over: RuleLike = cast(RuleLike, impl)
    over.is_name = True
    return impl


class rule:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.impl: Callable[..., Any] | None = None
        self.params: tuple[Any, ...] = ()
        self.kwparams: dict[str, Any] = {}
        self.ruleinfo: RuleInfo = RuleInfo(
            name='<none>',
            obj=None,
            impl=lambda: None,
            is_leftrec=False,
            is_memoizable=True,
            is_name=False,
            params=(),
            kwparams={},
        )

        # If the first argument is a callable and no other args exist,
        # it was used as @rule. Otherwise, it was @rule(...).
        if len(args) == 1 and callable(args[0]) and not kwargs:
            self.impl = args[0]
            return

        self.params = args
        self.kwparams = kwargs

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # If impl is None, we are in the @rule(...) phase
        if self.impl is None:
            impl: Callable[..., Any] = args[0]
            new = rule(*self.params, **self.kwparams)
            new.impl = impl
            functools.update_wrapper(new, impl)
            # Return a new instance with the implementation bound
            return new
        return self

        @functools.wraps(self.impl)
        def wrapper(obj: Any = None, ctx: Any = None) -> Any:
            return self._run(obj, ctx, args, kwargs)

        return wrapper
        # Otherwise, this is the actual function call
        # return self._run(None, None, args, kwargs)

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if obj is None:
            return self

        # Return a wrapper that binds 'self' (obj)
        if not callable(self.impl):
            return self

        self.ruleinfo = self._ruleinfo(obj, self.impl)
        self.impl.__ruleinfo__ = self.ruleinfo  # pyright: ignore[reportFunctionMemberAccess]

        # return self._run
        @functools.wraps(self.impl)
        def wrapper(obj: Any, ctx: Any = None) -> Any:
            return self._run(obj, ctx, (), {})

        return wrapper

    def _ruleinfo(self, obj: Any, impl: Callable[..., Any]) -> RuleInfo:
        name = impl.__name__  # type: ignore
        is_leftrec = getattr(impl, 'is_leftrec', False)
        is_memoizable = getattr(impl, 'is_memoizable', True)
        is_name = getattr(impl, 'is_name', False)

        return RuleInfo(
            name=name,
            obj=obj,
            impl=impl,
            is_leftrec=is_leftrec,
            is_memoizable=is_memoizable,
            is_name=is_name,
            params=self.params,
            kwparams=self.kwparams,
        )

    def _run(
        self,
        obj: Any,
        ctx: Any = None,
        _args: tuple[Any, ...] | None = None,
        _kwargs: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        assert obj, f'{obj=!r} {ctx=!r}'

        if isinstance(ctx, ParseContext):
            return ctx._call(self.ruleinfo)
        else:
            return obj._call(self.ruleinfo)  # legacy case
