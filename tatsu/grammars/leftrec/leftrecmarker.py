# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable
from enum import Enum, auto

from ..basic import Cut
from ..choice import Choice
from ..model import Box, Model, Rule
from ..syntax import Call, Sequence


__all__ = ['mark_left_recursion']


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


def mark_left_recursion(rules: Iterable[Rule]) -> list[Rule]:
    class State(Enum):
        FIRST = auto()
        VISITING = auto()
        VISITED = auto()

    rules = list(rules)
    rule_index = {rule.name: i for i, rule in enumerate(rules)}

    for rule in rules:
        rule.is_lrec = False
        rule.is_memo = not rule.no_memo

    edges = [_callable_rule_ids(rule.exp, rule_index) for rule in rules]

    state = [State.FIRST] * len(rules)
    stack: list[int] = []

    def dfs(rule_id: int) -> None:
        if state[rule_id] in {State.VISITING, State.VISITED}:
            return

        state[rule_id] = State.VISITING
        stack.append(rule_id)

        for child_id in edges[rule_id]:
            if state[child_id] == State.FIRST:
                dfs(child_id)
            elif state[child_id] == State.VISITING:
                rules[child_id].is_lrec = True
                rules[child_id].is_memo = False
                for rid in stack:
                    rules[rid].is_memo = False

        stack.pop()
        state[rule_id] = State.VISITED

    for i in range(len(rules)):
        dfs(i)

    return [rule for rule in rules if rule.is_lrec]
