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
    'BoundCallable',
    'NotNone',
    'NotNoneType',
    'Undefined',
    'UndefinedType',
    'boundcall',
]


def notnone[T](value: T | None, default: T) -> T:
    return value if value is not None else default


def boundcall(fun: Callable, known: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
    return BoundCallable.call(fun, known, *args, **kwargs)


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

    args: list[Any] = field(default_factory=list)
    arg_names: dict[str, Any] = field(default_factory=dict)
    kwargs: dict[str, Any] = field(default_factory=dict)

    def seen(self, name: str) -> bool:
        return name in self.arg_names or name in self.kwargs

    def empty(self) -> bool:
        return not (bool(self.args) or bool(self.kwargs))

    def add_arg(self, name: str, var: Any):
        self.arg_names[name] = var
        self.args.append(var)

    def add_kwarg(self, name: str, var: Any):
        self.kwargs[name] = var

    def add_args(self, args: Iterable[Any]):
        self.args.extend(args)

    def add_kwargs(self, kwargs: Mapping[str, Any]):
        self.kwargs.update(kwargs)


class BoundCallable:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-09)
    """
    Handles the binding of context-aware data to a callable's signature.
    """
    def __init__(self, fun: Callable, known: dict[str, Any], *args: Any, **kwargs: Any):
        self.fun = fun
        self.actual = self.bind(fun, known, *args, **kwargs)

    def __call__(self) -> Any:
        return self.fun(*self.actual.args, **self.actual.kwargs)

    @staticmethod
    def call(fun: Callable, known: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        actual = BoundCallable.bind(fun, known, *args, **kwargs)
        return fun(*actual.args, **actual.kwargs)

    @staticmethod
    def bind(fun: Callable, known: dict[str, Any], *args: Any, **kwargs: Any) -> ActualArguments:
        arg = next(iter(known.values())) if known else (args[0] if args else None)

        funname = getattr(fun, '__name__', None)
        if funname in vars(builtins):
            return ActualArguments(args=[arg])

        declared = inspect.signature(fun).parameters
        p = inspect.Parameter

        actual = ActualArguments()
        for name, value in known.items():
            if not (param := declared.get(name, None)):
                continue
            match param.kind:
                case p.POSITIONAL_ONLY:
                    actual.add_arg(name, value)
                case p.POSITIONAL_OR_KEYWORD:
                    actual.add_kwarg(name, value)
                case p.KEYWORD_ONLY:
                    actual.add_kwarg(name, value)

        argsc = list(args)
        kwargsc = kwargs.copy()
        for name, param in declared.items():
            if actual.seen(name):
                continue

            match param.kind:
                case p.POSITIONAL_ONLY:
                    actual.add_arg(name, argsc.pop(0) if argsc else arg)  # note: inject known arg
                case p.POSITIONAL_OR_KEYWORD:
                    if name in kwargsc:
                        actual.add_kwarg(name, kwargsc.pop(name, Undefined))
                    else:
                        actual.add_arg(name, argsc.pop(0))
                case p.KEYWORD_ONLY:
                    actual.add_kwarg(name, kwargsc.pop(name, Undefined))
                case p.VAR_POSITIONAL:
                    actual.add_args(argsc)
                case p.VAR_KEYWORD:
                    actual.add_kwargs(kwargs)

        return actual
