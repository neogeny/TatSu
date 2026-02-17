# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any, override

from tatsu import grammars
from tatsu.util.abctools import flatten
from tatsu.walkers import NodeWalker


def lines(model: grammars.Grammar):
    walker = RailroadNodeWalker()
    return walker.walk(model)


def draw(model: grammars.Grammar):
    for line in lines(model):
        print(line)


class RailroadNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    @override
    def walk(self, node: Any, *args, **kwargs) -> list[str]:
        return super().walk(node)

    def walk_decorator(self, decorator: grammars.Decorator) -> list[str]:
        return self.walk(decorator.exp)

    def walk_default(self, node: grammars.Model) -> list[str]:
        return [f'{node!r}']

    def walk_grammar(self, g: grammars.Grammar) -> list[str]:
        return flatten(self.walk(r) for r in g.rules)

    def assert_one_width(self, block: list[str]) -> list[str]:
        if not block:
            return []

        width = len(block[0])
        for rail in block:
            assert len(rail) == width
        return block

    def concatenate(self, left: list[str], right: list[str]) -> list[str]:
        if not right:
            return left.copy()
        if not left:
            return right.copy()

        left_width = len(left[0])
        right_width = len(right[0])
        final_height = max(len(left), len(right))
        common_height = min(len(left), len(right))

        out = left.copy()
        for i in range(final_height):
            if i < common_height:
                out[i] += right[i]
            elif i < len(out):
                out[i] += f'{' ' * right_width}'
            else:
                out += f'{' ' * left_width}{right[i]}'

        return self.assert_one_width(out)

    def walk_rule(self, rule: grammars.Rule) -> list[str]:
        out = [f'{rule.name}●━']
        return self.concatenate(out, self.walk(rule.exp))

    def walk_optional(self, o) -> list[str]:
        return ['']  # to be implemented

    def walk_closure(self, r) -> list[str]:
        return ['']  # to be implemented

    def walk_choice(self, c) -> list[str]:
        return ['']  # to be implemented

    def walk_sequence(self, s: grammars.Sequence) -> list[str]:
        out = []
        for element in s.sequence:
            out = self.concatenate(out, self.walk(element))
        return self.assert_one_width(out)

    def walk_call(self, call: grammars.Call) -> list[str]:
        return [f"→ {call.name} ─"]

    def walk_pattern(self, pattern: grammars.Pattern) -> list[str]:
        return [pattern.pattern]  # to be implemented

    def walk_token(self, token: grammars.Token) -> list[str]:
        return [f"→ {token.token} ─"]

    def walk_eof(self, eof: grammars.EOF) -> list[str]:
        return ["→ 🔚 ─"]

    def walk_lookahead(self, la: grammars.Lookahead) -> list[str]:
        return self.walk(la.exp)

    def walk_negative_lookahead(self, la: grammars.NegativeLookahead) -> list[str]:
        return self.walk(la.exp)

    def walk_void(self, v: grammars.Void) -> list[str]:
        return ["→ ∅ ─"]

    def walk_fail(self, v) -> list[str]:
        return ["→ ⚠ ─"]

    def walk_endrule(self, ast) -> list[str]:
        return ['']  # to be implemented

    def walk_emptyline(self, ast, *args) -> list[str]:
        return ['']  # to be implemented
