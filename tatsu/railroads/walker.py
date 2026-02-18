# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import override

from tatsu import grammars
from ..util.abctools import join_lists
from ..util.string import ulen
from ..walkers import NodeWalker


def lines(model: grammars.Grammar):
    walker = RailroadNodeWalker()
    return walker.walk(model)


def draw(model: grammars.Grammar):
    for line in lines(model):
        print(line.rstrip())


class RailroadNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    @override
    def walk(self, node: grammars.Model, *args, **kwargs) -> list[str]:
        return list(super().walk(node))

    def walk_decorator(self, decorator: grammars.Decorator) -> list[str]:
        return self.walk(decorator.exp)

    def walk_default(self, node: grammars.Model) -> list[str]:
        return [f' <{node!r}> ']

    def walk_grammar(self, grammar: grammars.Grammar) -> list[str]:
        return join_lists(*(self.walk(r) for r in grammar.rules))

    def assert_one_width(self, block: list[str]) -> list[str]:
        if not block:
            return []

        width = ulen(block[0])
        for rail in block:
            assert isinstance(rail, str), f'{rail=!r}'
            assert ulen(rail) == width
        return block

    def merge_choice(self, paths: list[list[str]]) -> list[str]:
        # by Gemini 2026/02/17

        if not paths:
            return []
        if len(paths) == 1:
            return [f"───{paths[0][0]}───"]

        max_w = max(ulen(p[0]) if p else 0 for p in paths)
        out = []

        # 3. Top Rail
        main = paths[0][0] if paths[0] else ''
        pad0 = "─" * (max_w - ulen(main))
        out.append(f"──┬─{main}{pad0}─┬─")

        # 4. Middle Paths
        for path in paths[1:-1]:
            mid = path[0]
            pad_m = "─" * (max_w - ulen(mid))
            out.append(f"  ├─{mid}{pad_m}─┤ ")

        # 5. Last Path
        last = paths[-1][0] if paths[-1] else ''
        pad_l = "─" * (max_w - ulen(last))
        out.append(f"  └─{last}{pad_l}─┘ ")

        return self.assert_one_width(out)

    def one_or_more_loop(self, path: list[str]) -> list[str]:
        # by Gemini 2026/02/17
        if not path:
            return ["───>───"]

        # 1. Dimensions
        max_w = max(ulen(line) for line in path)
        out = []

        # 2. First Line (The Entry Rail)
        # If path[0] is empty/blanks, this becomes the 'bypass'
        first = path[0]
        first_pad = "─" * (max_w - ulen(first))
        out.append(f"──┬─{first}{first_pad}─┬──")

        # 3. Middle Lines (The Body)
        for line in path[1:]:
            pad = " " * (max_w - ulen(line))
            out.append(f"  │ {line}{pad} │  ")

        # 4. The Loop Rail (The Return)
        # Standardized to 4 chars left, 4 chars right
        # To align ┘ perfectly under ┬, we match the suffix '─<┘ ' to '─┬──'
        loop_rail = "─" * max_w
        out.append(f"  └─{loop_rail}<┘  ")

        return self.assert_one_width(out)

    def zero_or_more_loop(self, path: list[str]) -> list[str]:
        loop = self.one_or_more_loop(path)
        return self.merge_choice([[], loop])
        # by Gemini 2026/02/17
        if not path:
            return ["───>───"]

        # 1. Dimensions
        max_w = max(len(line) for line in path)
        out = []

        # 2. Top Rail (The Bypass)
        # Left: ──┬── (5) | Right: ──┬── (5)
        # Total Width: max_w + 10
        top_rail = "─" * max_w
        out.append(f"──┬──{top_rail}──┬──")

        # 3. Content Body
        for i, line in enumerate(path):
            pad = " " * (max_w - len(line))

            if i == 0:
                # First line: Enters from the left, merges into the vertical on the right
                out.append(f"  └─>{line}{pad}──┘  ")
            else:
                # Middle lines: Keeps the vertical bar '│' going
                out.append(f"     {line}{pad}  │  ")

        return self.assert_one_width(out)

    def concatenate(self, left: list[str], right: list[str]) -> list[str]:
        assert isinstance(left, list), f'{left=!r}'
        assert isinstance(right, list), f'{right=!r}'

        if not right:
            return left.copy()
        if not left:
            return right.copy()

        left_width = ulen(left[0])
        right_width = ulen(right[0])
        final_height = max(len(left), len(right))
        common_height = min(len(left), len(right))

        out = left.copy()
        for i in range(final_height):
            if i < common_height:
                out[i] += right[i]
            elif i < len(out):
                out[i] += f'{' ' * right_width}'
            else:
                out += [f'{' ' * left_width}{right[i]}']

        return self.assert_one_width(out)

    def walk_rule(self, rule: grammars.Rule) -> list[str]:
        out = [f'{rule.name} ●─']
        out = self.concatenate(out, self.walk(rule.exp))
        out = self.concatenate(out, ['■'])
        out += [' ' * ulen(out[0])]
        return self.assert_one_width(out)

    # def walk_optional(self, o) -> list[str]:
    #     return ['']  # to be implemented
    #
    def walk_closure(self, closure: grammars.Closure) -> list[str]:
        return self.zero_or_more_loop(self.walk_decorator(closure))

    def walk_positive_closure(self, closure: grammars.Closure) -> list[str]:
        return self.one_or_more_loop(self.walk_decorator(closure))

    def walk_choice(self, choice: grammars.Choice) -> list[str]:
        return self.merge_choice([self.walk(o) for o in choice.options])

    def walk_option(self, option: grammars.Option) -> list[str]:
        return self.walk(option.exp)

    def walk_sequence(self, s: grammars.Sequence) -> list[str]:
        out = []
        for element in s.sequence:
            out = self.concatenate(out, self.walk(element))
        return self.assert_one_width(out)

    def walk_call(self, call: grammars.Call) -> list[str]:
        return [f" {call.name} "]

    def walk_pattern(self, pattern: grammars.Pattern) -> list[str]:
        return [pattern.pattern]  # to be implemented

    def walk_token(self, token: grammars.Token) -> list[str]:
        return [f"{token.token!r}"]

    def walk_eof(self, eof: grammars.EOF) -> list[str]:
        return ["🔚─"]

    def walk_lookahead(self, la: grammars.Lookahead) -> list[str]:
        out = self.concatenate(['&('], self.walk(la.exp))
        out = self.concatenate(out, [')'])
        return out

    def walk_negative_lookahead(self, la: grammars.NegativeLookahead) -> list[str]:
        out = self.concatenate(['!('], self.walk(la.exp))
        out = self.concatenate(out, [')'])
        return out

    def walk_void(self, v: grammars.Void) -> list[str]:
        return ["→ ∅ ─"]

    def walk_cut(self, cut: grammars.Cut) -> list[str]:
        return ["→ ~ ─"]

    def walk_fail(self, v) -> list[str]:
        return ["→ ⚠ ─"]

    # def walk_endrule(self, ast) -> list[str]:
    #     return ['']  # to be implemented
    #
    # def walk_emptyline(self, ast, *args) -> list[str]:
    #     return ['']  # to be implemented

    def walk_override(self, override: grammars.Override) -> list[str]:
        out = self.concatenate(['@:('], self.walk(override.exp))
        out = self.concatenate(out, [')'])
        return out

    def walk_constant(self, constant: grammars.Constant) -> list[str]:
        return [f'`{constant.literal}`']
