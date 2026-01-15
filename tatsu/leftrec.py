from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping
from enum import IntEnum, auto

from . import grammars
from .util import debug

# Based on https://github.com/ncellar/autumn_v1/


# Returns the correct Rule instance for a RuleRef
def follow_ref(node, rulemap):
    if isinstance(node, grammars.RuleRef):
        return rulemap.get(node.name, node)
    else:
        return node


def set_left_recursion(grammar):
    # Traversable state
    class State(IntEnum):
        FIRST = auto()
        CUTOFF = auto()
        VISITED = auto()

    state: MutableMapping[grammar.Rule, State] = defaultdict(lambda: State.FIRST)
    stack_depth = 0  # nonlocal workaround 2.7
    stack_position = {}
    lr_stack_positions = [-1]

    def walk(model):
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

        for c in model.at_same_pos(grammar.rulemap):
            child = follow_ref(c, grammar.rulemap)
            walk(child)
            # afterEdge
            if (
                state[child] == State.CUTOFF
                and stack_position[child] > lr_stack_positions[-1]
            ):
                # turn off memoization for all rules that were involved in this cycle
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

    for rule in grammar.children_list():
        walk(rule)

    # print()
    # for rule in grammar.children_list():
    #    print(rule)
    #    if rule.is_leftrec: print("-> Leftrec")
    #    if rule.is_nullable(): print("-> Nullable")
