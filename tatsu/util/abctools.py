# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import functools
import operator
from collections.abc import Callable, Iterable, Mapping
from itertools import zip_longest
from typing import Any, NamedTuple

type Predicate[K, V] = Callable[[K, V], bool]


def true(*_: Any, **__: Any) -> bool:
    return True


def is_list(o) -> bool:
    return type(o) is list


def to_list(o: Any) -> list[Any]:
    if o is None:
        return []
    elif isinstance(o, list):
        return o
    else:
        return [o]


def is_namedtuple(obj) -> bool:
    return (
        len(type(obj).__bases__) == 1
        and isinstance(obj, tuple)
        and hasattr(obj, '_asdict')
        and hasattr(obj, '_fields')
        and all(isinstance(f, str) for f in getattr(obj, '_fields', ()))
    )


def as_namedtuple(obj: Any) -> NamedTuple | None:
    if is_namedtuple(obj):
        return obj
    else:
        return None


def simplify_list(x) -> list[Any] | Any:
    if isinstance(x, list) and len(x) == 1:
        return simplify_list(x[0])
    return x


def extend_list(x: list[Any], n: int, default=None) -> None:
    def _null():
        pass

    default = default or _null

    missing = max(0, 1 + n - len(x))
    x.extend(default() for _ in range(missing))


def contains_sublist(lst: list[Any], sublst: list[Any]) -> bool:
    n = len(sublst)
    return any(sublst == lst[i : i + n] for i in range(1 + len(lst) - n))


def join_lists(*lists: list[Any]) -> list[Any]:
    return list(functools.reduce(operator.iadd, lists, []))


def flatten(o: Iterable[Any] | Any) -> list[Any]:
    def iterate(x: Any) -> Iterable[Any]:
        if not isinstance(o, list | tuple):
            yield x
            return

        for item in x:
            yield from flatten(item)

    return list(iterate(o))


def compress_seq(seq: Iterable[Any]) -> list[Any]:
    seen = set()
    result = []
    for x in seq:
        if x not in seen:
            result.append(x)
            seen.add(x)
    return result


def isiter(obj: Any) -> bool:
    """
    Check if an object is a non-string-like iterable suitable for JSON array conversion.
    # by Gemini (2026-01-26)
    # by [apalala@gmail.com](https://github.com/apalala)
    """
    if isinstance(obj, str | bytes | bytearray | Mapping):
        return False
    try:
        iter(obj)
        return True
    except (TypeError, AttributeError):
        return False


def prune_dict(d, predicate):
    """Remove all items x where predicate(x, d[x])"""

    keys = [k for k, v in d.items() if predicate(k, v)]
    for k in keys:
        del d[k]


def chunks(iterable, size, fillvalue=None):
    return zip_longest(*[iter(iterable)] * size, fillvalue=fillvalue)


def left_assoc(elements):
    if not elements:
        return ()

    it = iter(elements)
    expre = next(it)
    for e in it:
        op = e
        expre = (op, expre, next(it))
    return expre


def right_assoc(elements):
    if not elements:
        return ()

    def assoc(it):
        left = next(it)
        try:
            op = next(it)
        except StopIteration:
            return left
        else:
            return op, left, assoc(it)

    return assoc(iter(elements))


def rowselect[K, V](
    keys: Iterable[K],
    row: dict[K, V],
    *,
    where: Predicate[K, V] = true,
) -> dict[K, V]:
    # by [apalala@gmail.com](https://github.com/apalala)
    # by Gemini (2026-02-05)
    return {k: row[k] for k in keys if k in row and where(k, row[k])}


def select[K, V](
    keys: Iterable[K],
    *rows: dict[K, V],
    where: Predicate[K, V] = true,
) -> list[dict[K, V]]:
    return [rowselect(keys, row, where=where) for row in rows]
