# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Iterable, Iterator

from ..grammars import Grammar, Rule

type RuleName = str
type Headmap = dict[RuleName, set[RuleName]]
type SCC = set[RuleName]  # Strongly Connected Component


class GrammarAnalysis:
    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar
        self.head_map = self._build_head_map()
        self.grammar_order = {r.name: i for i, r in enumerate(self.grammar.rules)}
        self.sccs = self._build_sccs()
        self.recursive_rules = self._find_recursive_rules()

    def _get_rule(self, name: str) -> Rule:
        return self.grammar.rulemap[name]

    def rule_in_order_key(self, name: str) -> int:
        return self.grammar_order[name]

    def ordered_rule_names(self, names: Iterable[RuleName]) -> list[RuleName]:
        return sorted(names, key=self.rule_in_order_key)

    def _build_head_map(self) -> Headmap:
        def is_rule_name(element: str) -> bool:
            return element in self.grammar.rulemap

        return {
            rule.name: {
                str(la[0]) for la in rule.lookahead() if la and is_rule_name(str(la[0]))
            }
            for rule in self.grammar.rules
        }

    def _find_recursive_rules(self) -> set[RuleName]:
        def in_own_headmap(name) -> bool:
            return name in self.head_map.get(name, set())

        return set(filter(in_own_headmap, (r.name for r in self.grammar.rules)))

    # NOTE: Tarjan's Algorithm for Strongly Connected Components
    def _build_sccs(self) -> list[SCC]:
        index = 0
        stack: list[RuleName] = []
        indices: dict[RuleName, int] = {}
        lowlink: dict[RuleName, int] = {}
        on_stack: set[RuleName] = set()
        sccs: list[SCC] = []

        # Define what counts as a "Rule" vs a "Terminal"
        valid_rules = [r.name for r in self.grammar.rules]

        def strongconnect(v: RuleName) -> None:
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in self.head_map.get(v, set()):
                # Only traverse if the dependency is also a defined rule
                if w in valid_rules:
                    if w not in indices:
                        strongconnect(w)
                        lowlink[v] = min(lowlink[v], lowlink[w])
                    elif w in on_stack:
                        lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                component = set()
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.add(w)
                    if w == v:
                        break
                sccs.append(component)

        # Only start the walk from actual rules
        for rule_name in valid_rules:
            if rule_name not in indices:
                strongconnect(rule_name)

        return sccs

    # CAVEAT: this does not work in all leftrec cases
    def find_leaders_in_scc(self, scc: SCC) -> set[RuleName]:
        leaders = set(scc)
        for start in scc:
            # Try to find a leader such that all cycles go through it.
            for cycle in self.find_cycles_in_scc(scc, start):
                if len(cycle) > 2:
                    # leaders -= set(scc) - set(cycle)
                    leaders &= set(cycle)
                # if not leaders:
                #     break
                # raise ValueError(
                #     f"SCC {scc} {leaders} has no leadership candidate"
                #     " (no element is included in all cycles)"
                # )
        return leaders

    def find_cycles_in_scc(self, scc: SCC, start: RuleName) -> list[list[RuleName]]:
        """Find cycles in SCC emanating from start.

        Yields lists of the form ['A', 'B', 'C', 'A'], which means there's
        a path from A -> B -> C -> A.  The first item is always the start
        argument, but the last item may be another element, e.g.  ['A',
        'B', 'C', 'B'] means there's a path from A to B and there's a
        cycle from B to C and back.
        """
        # Basic input checks.
        assert start in scc, (start, scc)
        assert start in self.head_map, (start, scc)

        # Recursive helper that yields cycles.
        def dfs(node: RuleName, path: list[RuleName]) -> Iterator[list[str]]:
            if node in path:  # found a cycle
                yield [*path, node]
                return
            path = [*path, node]
            for child in self.head_map[node]:
                yield from dfs(child, path)

        return list(dfs(start, []))
