from __future__ import annotations

from collections import defaultdict
from enum import IntEnum, auto
from typing import cast

from tatsu import grammars

__all__ = ['mark_left_recursion']


# note: based on https://github.com/ncellar/autumn_v1/
def mark_left_recursion(grammar: grammars.Grammar) -> None:

    class State(IntEnum):
        FIRST = auto()
        CUTOFF = auto()
        VISITED = auto()

    depth = 0
    depth_stack: list[int] = [-1]
    node_depth: dict[grammars.Model, int] = {}
    node_state: dict[grammars.Model, State] = defaultdict(lambda: State.FIRST)

    def follow_ref(ref: grammars.Model | grammars.Rule) -> grammars.Rule:
        if isinstance(ref, grammars.RuleRef):
            return grammar.rulemap[ref]
        return cast(grammars.Rule, ref)

    def dfs(node: grammars.Model):
        nonlocal depth

        if node is None:
            raise ValueError('A None got here')
        depth += 1
        depth_stack.append(depth)

        if node_state[node] == State.FIRST:
            node_state[node] = State.CUTOFF
        else:
            return

        # beforeNode
        leftrec = isinstance(node, grammars.Rule) and node.is_leftrec
        if leftrec:
            depth_stack.append(depth)

        node_depth[node] = depth
        depth += 1

        callable_children = (
            follow_ref(c)
            for c in node.callable_at_same_pos(grammar.rulemap)
        )
        for child in callable_children:
            dfs(child)
            # afterEdge
            if (
                node_state[child] == State.CUTOFF and
                node_depth[child] > depth_stack[-1]
            ):
                # turn off memoization for all rules that were involved in this cycle
                child_rules = (n for n in node_depth if isinstance(n, grammars.Rule))
                for childrule in child_rules:
                    childrule.is_memoizable = False

                child.is_leftrec = True

        # afterNode
        if leftrec:
            depth_stack.pop()

        del node_depth[node]
        depth -= 1

        node_state[node] = State.VISITED

    for rule in grammar.rules:
        dfs(rule)
