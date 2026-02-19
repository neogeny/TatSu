# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import builtins
import inspect
import itertools
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from types import ModuleType
from typing import Any

from .itertools import CycleError, first, topsort

__all__ = [
    'ActualArguments',
    'BoundCallable',
    'Constructor',
    'TypeContainer',
    'boundcall',
]

type Constructor = type | Callable
type TypeContainer = type | ModuleType | Mapping[str, type] | dict[str, type]


def boundcall(fun: Callable, known: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
    return BoundCallable.call(fun, known, *args, **kwargs)


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
        if name in self.arg_names:
            return
        self.arg_names[name] = var
        self.args.append(var)

    def add_kwarg(self, name: str, var: Any):
        if name in self.arg_names:
            return
        self.kwargs[name] = var

    def add_args(self, args: Iterable[Any]):
        self.args.extend(args)

    def add_kwargs(self, kwargs: Mapping[str, Any]):
        self.kwargs.update(kwargs)

    def unique(self) -> ActualArguments:
        clone = replace(self)
        for name in list(clone.kwargs):
            if name in clone.arg_names:
                del clone.kwargs[name]
        return clone


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
    def bind(
        fun: Callable, known: dict[str, Any], *args: Any, **kwargs: Any
    ) -> ActualArguments:
        arg = next(iter(known.values())) if known else (args[0] if args else None)

        funname = getattr(fun, '__name__', None)
        if funname in vars(builtins):
            return ActualArguments(args=[arg])

        declared = inspect.signature(fun).parameters
        p = inspect.Parameter

        actual = ActualArguments()
        argsc = list(args)
        kwargsc = kwargs.copy()
        for name, param in declared.items():
            if actual.seen(name):
                continue

            match param.kind:
                case p.KEYWORD_ONLY:
                    actual.add_kwarg(name, kwargsc.pop(name, None))
                case p.POSITIONAL_OR_KEYWORD:
                    if name in kwargsc:
                        actual.add_kwarg(name, kwargsc.pop(name, None))
                    else:
                        actual.add_arg(name, argsc.pop(0) if argsc else arg)
                case p.POSITIONAL_ONLY:
                    actual.add_arg(
                        name, argsc.pop(0) if argsc else arg
                    )  # note: inject known arg
                case p.VAR_POSITIONAL:
                    actual.add_args(argsc)
                case p.VAR_KEYWORD:
                    actual.add_kwargs(kwargs)

        for name, value in known.items():
            if not (param := declared.get(name, None)):
                continue
            match param.kind:
                case p.KEYWORD_ONLY:
                    actual.add_kwarg(name, value)
                case p.POSITIONAL_OR_KEYWORD:
                    actual.add_kwarg(name, value)
                case p.POSITIONAL_ONLY:
                    actual.add_arg(name, value)

        return actual.unique()


def least_upper_bound_type(constructors: Sequence[Constructor]) -> type:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-01-30)

    # Caller is responsible for filtering constructors to relevant types
    types_ = [t for t in constructors if isinstance(t, type)]

    if not types_:
        return object
    if len(types_) == 1:
        return types_[0]

    nodes: set[type] = set()
    edges: set[tuple[type, type]] = set()

    for t in types_:
        # mro[1:] focuses on the skeleton/ancestors
        ancestors = t.__mro__[1:]
        nodes.update(ancestors)

        edges.update((child, parent) for child, parent in itertools.pairwise(ancestors))

    if not nodes:
        return object

    try:
        topsorted = topsort(list(nodes), list(edges))
    except CycleError:
        return object

    # The LUB is the most specific ancestor that covers all provided types
    # Since child -> parent, we check from the most specific in the sort
    return first(
        (parent for parent in topsorted if all(issubclass(t, parent) for t in types_)),
        default=object,
    )
