# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# by Vic Nightfall <vic nightfall.moe > 2019
from __future__ import annotations

from collections import defaultdict
from enum import Enum, auto
from typing import cast

from .._core import Model, Rule


__all__ = ['mark_left_recursion']


# note: based on https://github.com/ncellar/autumn_v1/
def mark_left_recursion(rules: list[Rule]) -> list[Rule]:

    class State(Enum):
        FIRST = auto()
        CUTOFF = auto()
        VISITED = auto()

    leftrec_rules: list[Rule] = []
    depth = 0
    depth_stack: list[int] = [-1]
    node_depth: dict[Model, int] = {}
    node_state: dict[Model, State] = defaultdict(lambda: State.FIRST)

    def dfs(node: Model):
        nonlocal depth

        if node_state[node] != State.FIRST:
            return
        node_state[node] = State.CUTOFF

        # beforeNode
        leftrec = isinstance(node, Rule) and node.is_leftrec
        if leftrec:
            depth_stack.append(depth)

        node_depth[node] = depth
        depth += 1
        try:
            callable_children = tuple(
                c.follow_ref() for c in node.callable_at_same_pos()
            )
            for child in callable_children:
                dfs(child)
                # afterEdge
                if (
                    node_state[child] == State.CUTOFF
                    and node_depth[child] > depth_stack[-1]
                ):
                    # turn off memoization for all rules that were involved in this cycle
                    child = cast(Rule, child)
                    child_rules = (n for n in node_depth if isinstance(n, Rule))
                    for childrule in child_rules:
                        childrule.is_memoizable = False

                    nonlocal leftrec_rules
                    assert isinstance(child, Rule)
                    child.is_leftrec = True
                    leftrec_rules.append(child)
        finally:
            # afterNode
            if leftrec:
                depth_stack.pop()
            del node_depth[node]
            depth -= 1
            node_state[node] = State.VISITED

    for rule in rules:
        dfs(rule)
    return leftrec_rules
