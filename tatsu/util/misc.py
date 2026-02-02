from __future__ import annotations

import importlib.util
import itertools
import re
import shutil
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from functools import cache
from graphlib import TopologicalSorter
from typing import Any

from .notnone import Undefined

type Constructor = Callable[..., Any]


class CycleError(ValueError):
    pass


def first(iterable: Iterable[Any], default=Undefined) -> Any:
    """Return the first item of *iterable*, or *default* if *iterable* is
    empty.

        >>> first([0, 1, 2, 3])
        0
        >>> first([], 'some default')
        'some default'

    If *default* is not provided and there are no items in the iterable,
    raise ``ValueError``.

    :func:`first` is useful when you have a generator of expensive-to-retrieve
    values and want any arbitrary one. It is marginally shorter than
    ``next(iter(iterable), default)``.

    """
    # NOTE: https://more-itertools.readthedocs.io/en/stable/_modules/more_itertools/more.html#first
    try:
        return next(iter(iterable))
    except StopIteration as e:
        # I'm on the edge about raising ValueError instead of StopIteration. At
        # the moment, ValueError wins, because the caller could conceivably
        # want to do something different with flow control when I raise the
        # exception, and it's weird to explicitly catch StopIteration.
        if default is Undefined:
            raise ValueError(
                'first() was called on an empty iterable, and no '
                'default value was provided.',
            ) from e
        return default


def find_from_rematch(m: re.Match):
    if m is None:
        return None
    g = m.groups(default=m.string[0:0])
    if len(g) == 1:
        return g[0]
    else:
        return g or m.group()


def iter_findall(pattern, string, pos=None, endpos=None, flags=0):
    """
    like finditer(), but with return values like findall()

    implementation taken from cpython/Modules/_sre.c/findall()
    """
    r = (
        pattern
        if isinstance(pattern, re.Pattern)
        else re.compile(pattern, flags=flags)
    )
    if endpos is not None:
        iterator = r.finditer(string, pos=pos, endpos=endpos)
    elif pos is not None:
        iterator = r.finditer(string, pos=pos)
    else:
        iterator = r.finditer(string)
    for m in iterator:
        yield find_from_rematch(m)


def findfirst(pattern, string, pos=None, endpos=None, flags=0, default=Undefined) -> str:
    """
    Avoids using the inefficient findall(...)[0], or first(findall(...))
    """
    return first(
        iter_findall(pattern, string, pos=pos, endpos=endpos, flags=flags),
        default=default,
    )


def topsort[T](nodes: Iterable[T], edges: Iterable[tuple[T, T]]) -> list[T]:
    # https://en.wikipedia.org/wiki/Topological_sorting

    # NOTE:
    #   topsort uses a partial order relationship,
    #   so results for the same arguments may be
    #   different from one call to the other
    #   _
    #   use this to make results stable accross calls
    #       topsort(n, e) == topsort(n, e)

    nodes = list(nodes)
    original_key = {node: i for i, node in enumerate(nodes)}

    def order_key(node: T) -> int:
        return original_key[node]

    partial_order = set(edges)

    def with_incoming() -> set[T]:
        nonlocal partial_order
        return {m for (_, m) in partial_order}

    result: list[T] = []
    pending = sorted(set(nodes) - with_incoming(), key=order_key, reverse=True)
    while pending:
        n = pending.pop()
        result.append(n)

        outgoing = {m for (x, m) in partial_order if x == n}
        partial_order -= {(n, m) for m in outgoing}
        pending.extend(outgoing - with_incoming())
        pending.sort(key=order_key, reverse=True)

    if partial_order:
        raise CycleError(f'There are cycles in {partial_order=!r}')

    return list(result)


def _graphlib_topsort[T](nodes: Iterable[T], edges: Iterable[tuple[T, T]]) -> list[T]:
    graph: dict[T, list[T]] = defaultdict(list[T], {n: [] for n in nodes})
    for (n, m) in edges:
        graph[m].append(n)

    sorter = TopologicalSorter(graph)
    return list(sorter.static_order())


@cache
def cached_re_compile(
        pattern: str | bytes | re.Pattern, /,
        escape: bool = False,
        flags: int = 0,
    ) -> re.Pattern:
    if isinstance(pattern, re.Pattern):
        return pattern
    pattern = str(pattern)
    if escape:
        pattern = re.escape(pattern)
    return re.compile(pattern, flags=flags)


def module_available(name):
    return importlib.util.find_spec(name) is not None


def module_missing(name):
    return not module_available(name)


def platform_has_command(name) -> bool:
    return shutil.which(name) is not None


def fqn(obj: Any) -> str:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-01-30)

    """Helper to safely retrieve the fully qualified name of a callable."""
    module = getattr(obj, "__module__", None)
    qualname = getattr(obj, "__qualname__", None)

    if module and qualname and module != "builtins":
        return f"{module}.{qualname}"
    return qualname or str(obj)


def typename(obj: Any) -> str:
    return type(obj).__name__


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
        (
            parent for parent in topsorted
            if all(issubclass(t, parent) for t in types_)
        ),
        default=object,
    )
