from __future__ import annotations

import importlib.util
import re
import shutil
from collections import defaultdict
from collections.abc import Iterable
from functools import cache
from graphlib import TopologicalSorter

from tatsu.util import Undefined


def first(iterable, default=Undefined):
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


def match_to_find(m: re.Match):
    if m is None:
        return None
    g = m.groups(default=m.string[0:0])
    if len(g) == 1:
        return g[0]
    else:
        return g or m.group()


def findalliter(pattern, string, pos=None, endpos=None, flags=0):
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
        yield match_to_find(m)


def findfirst(pattern, string, pos=None, endpos=None, flags=0, default=Undefined):
    """
    Avoids using the inefficient findall(...)[0], or first(findall(...))
    """
    return first(
        findalliter(pattern, string, pos=pos, endpos=endpos, flags=flags),
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
    original_keys = {node: i for i, node in enumerate(nodes)}

    def original_order(nl: Iterable[T]) -> list[T]:
        return sorted(nl, key=lambda x: original_keys[x])

    partial_order = set(edges)

    def with_incoming() -> set[T]:
        return {m for (_, m) in partial_order}

    result: list[T] = []
    pending = original_order(set(nodes) - with_incoming())
    while pending:
        n = pending.pop(0)
        result.append(n)

        outgoing = {m for (x, m) in partial_order if x == n}
        partial_order -= {(n, m) for m in outgoing}
        pending.extend(original_order(outgoing - with_incoming()))

    if partial_order:
        raise ValueError('There are cycles in the topological order')

    return list(result)


def _graphlib_topsort[T](nodes: Iterable[T], edges: Iterable[tuple[T, T]]) -> list[T]:
    graph: dict[T, list[T]] = defaultdict(list[T], {n: [] for n in nodes})
    for (n, m) in edges:
        graph[m].append(n)

    sorter = TopologicalSorter(graph)
    return list(sorter.static_order())


@cache
def cached_re_compile(regex: re.Pattern | str | bytes) -> re.Pattern | None:
    if isinstance(regex, re.Pattern):
        return regex
    return re.compile(regex) if isinstance(regex, (str | bytes)) else None


def module_available(name):
    return importlib.util.find_spec(name) is not None


def module_missing(name):
    return not module_available(name)


def platform_has_command(name) -> bool:
    return shutil.which(name) is not None
