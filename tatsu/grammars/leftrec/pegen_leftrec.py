# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

# noqa # type: ignore # ruff: noqa
# ty: ignore
# pyrefly: ignore
# pyright: ignore
# pyright: reportGeneralTypeIssues=false
# pyrefly: ignore-errors

from collections.abc import Iterable

from ..basic import Cut
from ..choice import Choice
from ..model import Box, Model, Rule
from ..syntax import Call, Sequence
from . import sccutils


__all__ = ['mark_left_recursion_pegen']


def _callable_rule_ids(exp: Model, rule_index: dict[str, int]) -> list[int]:
    if isinstance(exp, Call):
        target = rule_index.get(exp.name)
        return [target] if target is not None else []

    if isinstance(exp, Choice):
        result: list[int] = []
        for opt in exp.options:
            result.extend(_callable_rule_ids(opt, rule_index))
        return result

    if isinstance(exp, Sequence):
        result = []
        for item in exp.sequence:
            if isinstance(item, Cut):
                continue
            result.extend(_callable_rule_ids(item, rule_index))
            if not _is_nullable_safe(item):
                break
        return result

    if isinstance(exp, Box):
        return _callable_rule_ids(exp.exp, rule_index)

    return []


def _is_nullable_safe(exp: Model) -> bool:
    if isinstance(exp, Call):
        return False

    if isinstance(exp, Sequence):
        return all(_is_nullable_safe(item) for item in exp.sequence)

    if isinstance(exp, Choice):
        return any(_is_nullable_safe(opt) for opt in exp.options)

    return exp.is_nullable()


def _make_first_graph(
    rules: list[Rule], rule_index: dict[str, int]
) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for rule in rules:
        graph[rule.name] = {
            rules[i].name for i in _callable_rule_ids(rule.exp, rule_index)
        }

    all_vertices: set[str] = set(graph.keys())
    for deps in graph.values():
        all_vertices.update(deps)
    for v in all_vertices:
        graph.setdefault(v, set())

    return graph


def mark_left_recursion_pegen(rules: Iterable[Rule]) -> list[Rule]:
    rules = list(rules)
    rule_index = {rule.name: i for i, rule in enumerate(rules)}

    for rule in rules:
        rule.is_lrec = False
        rule.is_memo = not rule.no_memo

    graph = _make_first_graph(rules, rule_index)

    # pyrefly: ignore [bad-argument-type]
    sccs = list(sccutils.strongly_connected_components(set(graph.keys()), graph))  # pyright: ignore[reportArgumentType]  # ty:ignore[invalid-argument-type]

    for scc in sccs:
        if len(scc) > 1:
            for name in scc:
                rules[rule_index[name]].is_memo = False

            leaders = set(scc)
            for start in scc:
                for cycle in sccutils.find_cycles_in_scc(graph, scc, start):  # pyright: ignore[reportArgumentType]  # ty:ignore[invalid-argument-type]
                    leaders -= scc - set(cycle)
                    if not leaders:
                        break
                if not leaders:
                    break

            if not leaders:
                leaders = set(scc)

            leader_name = min(leaders)
            rules[rule_index[leader_name]].is_lrec = True

        elif len(scc) == 1:
            name = min(scc)
            if name in graph.get(name, set()):
                rule = rules[rule_index[name]]
                rule.is_lrec = True
                rule.is_memo = False

    return [rule for rule in rules if rule.is_lrec]
