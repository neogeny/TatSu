# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

"""
Define the non-AST semantics parging.

A CST is used to gather the values returned by expressions into the value
returned from a grammar rule invocation.

If a CST is to be returned from a grammar rule invocation, it is first converted
to a `tuple` (elseqwhere) so it doesn't play these games.
"""

import copy
from typing import Any


class closedlist(list[Any]):
    """
    A `list` that is not a list.

    It's used by closures and friends to keep their results as values that
    don't get merged with other lists.
    """

    __setitem__ = None  # type: ignore
    __delitem__ = None  # type: ignore
    __iadd__ = None  # type: ignore
    insert = None  # type: ignore

    def __hash__(self) -> int:  # type: ignore
        return hash(tuple(self))


def islist(o: Any) -> bool:
    return not isinstance(o, closedlist) and isinstance(o, list)


def cstfinal(cst: Any) -> Any:
    return closedlist(cst) if islist(cst) else cst


def cstadd(cst: Any, node: Any, aslist: bool = False) -> Any:
    """
    This is how the values of subexpressions are added to the result of the
    enclosing context: a rule, group, closure, ...
    :param cst: the previous CST value
    :param node: the node to add
    :param aslist: for rules that require that the final CST is a list
    :return: the new CST value
    """
    if cst is None:
        return [node] if aslist else copy.copy(node)
    if islist(cst):
        return [*cst, node]
    return [cst, node]


def cstmerge(cst: Any, other: Any) -> Any:
    """
    Used to merge the CST of a subexpression into the CST of the enclosing
    context.
    :param cst: the "outer" CST
    :param other: the CST to merge
    :return: the merged CST
    """
    if other is None:
        return cst
    if cst is None:
        return copy.copy(other)  # avoid shared state of lists
    if islist(other) and islist(cst):
        return cst + other
    if islist(other):
        return [cst, *other]
    if islist(cst):
        return [*cst, other]
    return [cst, other]
