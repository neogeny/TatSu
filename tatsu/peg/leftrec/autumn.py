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
        CUTOFF = auto()
        VISITED = auto()

    rules = list(rules)
    rule_index = {rule.name: i for i, rule in enumerate(rules)}

    # Reset initial structural properties
    for rule in rules:
        rule.is_lrec = False
        rule.is_memo = not rule.no_memo

    # Map the rule expressions directly to target rule integers
    edges = [_callable_rule_ids(rule.exp, rule_index) for rule in rules]

    # Depth tracking parameters
    depth = 0
    depth_stack: list[int] = [-1]
    rule_depth: dict[int, int] = {}
    rule_state: list[State] = [State.FIRST] * len(rules)

    def dfs(rule_id: int) -> None:
        nonlocal depth

        if rule_state[rule_id] == State.FIRST:
            rule_state[rule_id] = State.CUTOFF
        else:
            return

        # Frame boundaries setup for an already marked recursive branch
        is_already_lrec = rules[rule_id].is_lrec
        if is_already_lrec:
            depth_stack.append(depth)

        rule_depth[rule_id] = depth
        depth += 1

        try:
            for child_id in edges[rule_id]:
                dfs(child_id)

                # Evaluate loop closures against dynamic stack depth boundaries
                if (
                    rule_state[child_id] == State.CUTOFF
                    and rule_depth[child_id] > depth_stack[-1]
                ):
                    # Flag the loop closing point as left-recursive
                    rules[child_id].is_lrec = True

                    # Surgical un-memoization of loop context parameters
                    for active_id in rule_depth:
                        rules[active_id].is_memo = False

        finally:
            # Unwind scope depth tracking parameters cleanly
            if is_already_lrec:
                depth_stack.pop()
            rule_depth.pop(rule_id, None)
            depth -= 1
            rule_state[rule_id] = State.VISITED

    # Execute the depth-framed sweep over every rule
    for i in range(len(rules)):
        dfs(i)

    return [rule for rule in rules if rule.is_lrec]
