# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import builtins
import inspect
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, cast

__all__ = [
    'ActualArguments',
    'NotNone',
    'NotNoneType',
    'Undefined',
    'UndefinedType',
]


def notnone[T](value: T | None, default: T) -> T:
    return value if value is not None else default


class NotNoneType[T]:
    __notnone: Any = None

    def __init__(self):
        if isinstance(self.__notnone, NotNoneType):
            return
        type(self).__notnone = self

    @classmethod
    def notnone(cls) -> NotNoneType[T]:
        return cast(NotNoneType[T], cls.__notnone)

    def __eq__(self, other: Any) -> bool:
        if self is not Undefined:
            return False
        if other is not Undefined:
            return False
        return other is self

    def __bool__(self):
        return False

    def __and__(self, other):
        return self

    def __rand__(self, other):
        return self.__and__(other)

    def __or__(self, other):
        return other

    def __ror__(self, other):
        return self.__or__(other)

    def __invert__(self):
        return not None

    def __repr__(self) -> str:
        return super().__repr__()

    def __str__(self) -> str:
        return 'Undefined'

    def __hash__(self) -> int:
        return hash(id(self))


UndefinedType = NotNoneType
NotNone: NotNoneType[Any] = NotNoneType()
Undefined = NotNone


@dataclass
class ActualArguments:
    """
    A DTO representing the resolved positional and keyword arguments for a call.
    """
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-09)

    params: list[Any] = field(default_factory=list)
    param_names: dict[str, Any] = field(default_factory=dict)
    kwparams: dict[str, Any] = field(default_factory=dict)

    def has_any_params(self) -> bool:
        return bool(self.params) or bool(self.kwparams)

    def add_param(self, name: str, var: Any):
        self.param_names[name] = var
        self.params.append(var)

    def add_kwparam(self, name: str, var: Any):
        self.param_names[name] = var
        self.kwparams[name] = var

    def add_args(self, args: Iterable[Any]):
        self.params.extend(args)

    def add_kwargs(self, kwargs: Mapping[str, Any]):
        self.kwparams.update(kwargs)


class BoundCallable:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-09)
    """
    Handles the binding of context-aware data to a callable's signature.
    """
    def __init__(
            self,
            fun: Callable,
            known: dict[str, Any],
            *args: Any,
            **kwargs: Any,
    ):
        self.fun = fun
        self.actual = self.bind(fun, known, *args, **kwargs)

    def __call__(self) -> Any:
        return self.fun(*self.actual.params, **self.actual.kwparams)

    @staticmethod
    def call(
            fun: Callable,
            known: dict[str, Any],
            *args: Any,
            **kwargs: Any,
    ) -> Any:
        actual = BoundCallable.bind(fun, known, *args, **kwargs)
        return fun(*actual.params, **actual.kwparams)

    @staticmethod
    def bind(
            fun: Callable,
            known: dict[str, Any],
            *args: Any,
            **kwargs: Any,
    ) -> ActualArguments:
        arg = next(iter(known.values())) if known else (args[0] if args else None)

        if getattr(fun, '__name__', None) in vars(builtins):
            return ActualArguments(params=[arg])

        is_bound = inspect.ismethod(fun)
        sig = inspect.signature(fun)
        declared = sig.parameters

        actual = ActualArguments()
        P = inspect.Parameter
        for name, param in declared.items():
            if name not in known:
                continue

            value = known[name]
            match param.kind:
                case P.POSITIONAL_ONLY:
                    actual.add_param(name, value)
                case P.KEYWORD_ONLY | P.POSITIONAL_OR_KEYWORD:
                    actual.add_kwparam(name, value)

        for name, param in declared.items():
            if name in known or name in actual.param_names:
                continue

            if name == 'self' and not is_bound:
                continue

            match param.kind:
                case P.POSITIONAL_ONLY:
                    actual.add_param(name, arg)
                case P.POSITIONAL_OR_KEYWORD:
                    actual.add_kwparam(name, arg)
                case P.VAR_POSITIONAL:
                    actual.add_args(args)
                case P.VAR_KEYWORD:
                    actual.add_kwargs(kwargs)

        return actual
