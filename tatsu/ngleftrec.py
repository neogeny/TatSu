from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from tatsu.codegen.python import NegativeLookahead
from tatsu.grammars import (
    EOF,
    Any,
    Choice,
    Closure,
    Comment,
    Constant,
    Cut,
    Decorator,
    EmptyClosure,
    Fail,
    Gather,
    Grammar,
    Join,
    Lookahead,
    Model,
    Optional,
    Pattern,
    RuleRef,
    Sequence,
    SkipTo,
    Token,
    Void,
    ffset,
)

type RuleName = str
type SCC = list[RuleName]


def mark_recursive_rules(grammar: Grammar) -> None:
    analyzer = LeftRecursionAnalyzer(grammar)
    analyzer.mark_recursive_rules()


class LeftRecursionAnalyzer:
    def __init__(self, tatsu_grammar: Grammar) -> None:
        self.grammar = tatsu_grammar
        # FIXME: this is not use because of Model.lookahead()
        self.nullables: set[RuleName] = self._compute_nullables()
        self.head_map: Mapping[RuleName, set[RuleName]] = self._compute_head_map()

    # FIXME: not used
    def __old_mark_recursive_rules(self) -> None:
        print('nullables', self.nullables)
        print('headmap', self.head_map)
        recursive_set = self.find_left_recursion()
        print('recursive', recursive_set)
        for name, rule in self.grammar.rulemap.items():
            rule.is_leftrec = name in recursive_set
            rule.is_memoizable &= not name in recursive_set

    # FIXME: this is not use because of Model.lookahead()
    def _is_nullable(self, exp: Model | str) -> bool:  # noqa: PLR0911, PLR0912
        match exp:
            case str(name):
                return name in self.nullables
            case EOF():
                return False
            case Void():
                return True
            case Fail():
                return False
            case Cut():
                return True
            case Any():
                return False
            case SkipTo():
                return False
            case Comment():
                return True
            case Token():
                return False
            case Constant():
                return False
            case EmptyClosure():
                return True
            case Pattern() as p:
                return p._nullable()
            case Optional() | Closure() | Gather() | Join():
                return True
            case Lookahead(), NegativeLookahead():
                return True
            case Choice(options=options):
                return any(self._is_nullable(opt) for opt in options)
            case Sequence(sequence=items):
                return all(self._is_nullable(item) for item in items)
            case RuleRef(name=name):
                return name in self.nullables
            case Decorator(exp=inner):
                return self._is_nullable(inner)
            case _:
                return False

    # FIXME: this is not use because of Model.lookahead()
    def _compute_nullables(self) -> set[RuleName]:
        nullables: set[RuleName] = set()
        prev_size = -1
        while len(nullables) > prev_size:
            prev_size = len(nullables)
            self.nullables = nullables
            for name, rule in self.grammar.rulemap.items():
                if name not in nullables and self._is_nullable(rule.exp):
                    nullables.add(name)
        return nullables

    # FIXME: not used
    def _unused_get_heads(self, exp: Model | str) -> set[RuleName]:
        heads: set[RuleName] = set()

        match exp:
            case str(name):
                heads.add(name)
            case Token(token=token):
                heads.add(token)
            case Pattern(pattern=pattern):
                heads.add(pattern)
            case Constant(literal=literal):
                heads.add(literal)
            case Choice(options=options):
                for opt in options:
                    heads.update(self._get_heads(opt))
            case Sequence(sequence=items):
                for item in items:
                    if not self._is_nullable(item):
                        heads.update(self._get_heads(item))
                        break
            case Decorator(exp=inner):
                heads.update(self._get_heads(inner))

        return heads

    def _compute_head_map(self) -> dict[RuleName, set[Any]]:
        # map = {}
        # oldmap = {None: None}
        # while map != oldmap:
        #     oldmap = map.copy()
        #     map = {
        #         name: self._get_heads(rule.exp)
        #         for name, rule in self.grammar.rulemap.items()
        #     }
        #
        map: dict[RuleName, set[str]] = {
            rule.name: {fa[0] if fa else 'None' for fa in rule.lookahead()}
            for rule in self.grammar.rules
        }
        print('lookaheads', map)
        return map

    def compute_sccs(self) -> list[SCC]:
        index = 0
        stack: list[RuleName] = []
        indices: dict[RuleName, int] = {}
        lowlink: dict[RuleName, int] = {}
        on_stack: set[RuleName] = set()
        sccs: list[SCC] = []

        def strongconnect(v: RuleName) -> None:
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in self.head_map.get(v, []):
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                component: SCC = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.append(w)
                    if w == v:
                        break
                sccs.append(component)

        for rule_name in self.grammar.rulemap:
            if rule_name not in indices:
                strongconnect(rule_name)

        return sccs

    def mark_recursive_rules(self) -> None:
        sccs = self.compute_sccs()

        print('sccs', sccs)
        for component in sccs:
            for i, name in enumerate(component):
                if not (rule := self.grammar.rulemap.get(name)):
                    continue
                rule.is_memoizable = False
                if i == 0:
                    rule.is_leftrec = True
