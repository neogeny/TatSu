from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping
from enum import IntEnum, auto
from typing import cast

from . import grammars
from .util import debug

# Based on https://github.com/ncellar/autumn_v1/


def set_left_recursion(grammar: grammars.Grammar) -> None:
    # Traversable state
    class State(IntEnum):
        FIRST = auto()
        CUTOFF = auto()
        VISITED = auto()

    state: MutableMapping[grammars.Model, State] = defaultdict(lambda: State.FIRST)
    stack_depth = 0  # nonlocal workaround 2.7
    stack_position = {}
    lr_stack_positions = [-1]

    def dfs(model: grammars.Model):
        nonlocal stack_depth

        if state[model] == State.FIRST:
            state[model] = State.CUTOFF
        else:
            return

        # beforeNode
        leftrec = isinstance(model, grammars.Rule) and model.is_leftrec
        if leftrec:
            lr_stack_positions.append(stack_depth)

        stack_position[model] = stack_depth
        stack_depth += 1

        for c in model.callable_at_same_pos(grammar.rulemap):
            child = c.follow_ref(grammar.rulemap)
            dfs(child)
            # afterEdge
            if (
                state[child] == State.CUTOFF
                and stack_position[child] > lr_stack_positions[-1]
            ):
                # turn off memoization for all rules that were involved in this cycle
                child = cast(grammars.Rule, child)
                for rule in stack_position:
                    if isinstance(rule, grammars.Rule):
                        rule.is_memoizable = False

                child.is_leftrec = True
                debug(child.name)

        # afterNode
        if leftrec:
            lr_stack_positions.pop()

        del stack_position[model]
        stack_depth -= 1

        state[model] = State.VISITED

    for rule in grammar.rules:
        dfs(rule)
