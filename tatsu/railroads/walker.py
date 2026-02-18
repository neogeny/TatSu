# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import override

from tatsu import grammars

from ..util.abctools import join_lists
from ..util.string import unicode_display_len as ulen
from ..walkers import NodeWalker
from .railmath import check_same_len, lay_out, loop, stopnloop, weld


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

    def walk_default(self, node: grammars.Model) -> list[str]:
        return [f' <{node!r}> ']

    def walk_decorator(self, decorator: grammars.Decorator) -> list[str]:
        return self.walk(decorator.exp)

    def walk_grammar(self, grammar: grammars.Grammar) -> list[str]:
        return join_lists(*(self.walk(r) for r in grammar.rules))

    def walk_rule(self, rule: grammars.Rule) -> list[str]:
        out = [f'{rule.name} ●─']
        out = weld(out, self.walk(rule.exp))
        out = weld(out, ['■'])
        out += [' ' * ulen(out[0])]
        return check_same_len(out)

    def walk_optional(self, optional: grammars.Optional) -> list[str]:
        # return merge([self.walk(optional.exp), ['→']])
        out = weld(['→'], self.walk(optional.exp))
        return lay_out([out, ['→']])

    def walk_closure(self, closure: grammars.Closure) -> list[str]:
        return loop(self.walk_decorator(closure))

    def walk_positive_closure(self, closure: grammars.Closure) -> list[str]:
        return stopnloop(self.walk_decorator(closure))

    def walk_join(self, join: grammars.Join) -> list[str]:
        out = weld(self.walk(join.sep), self.walk(join.exp))
        return loop(out)

    def walk_positive_join(self, join: grammars.PositiveJoin) -> list[str]:
        out = weld(self.walk(join.sep), self.walk(join.exp))
        return stopnloop(out)

    def walk_choice(self, choice: grammars.Choice) -> list[str]:
        return lay_out([self.walk(o) for o in choice.options])

    def walk_option(self, option: grammars.Option) -> list[str]:
        return self.walk(option.exp)

    def walk_sequence(self, s: grammars.Sequence) -> list[str]:
        out = []
        for element in s.sequence:
            out = weld(out, self.walk(element))
        return check_same_len(out)

    def walk_call(self, call: grammars.Call) -> list[str]:
        return [f"{call.name}"]

    def walk_pattern(self, pattern: grammars.Pattern) -> list[str]:
        return [pattern.pattern]  # to be implemented

    def walk_token(self, token: grammars.Token) -> list[str]:
        return [f"─{token.token!r}─"]

    def walk_eof(self, eof: grammars.EOF) -> list[str]:
        return ["🔚 "]

    def walk_lookahead(self, la: grammars.Lookahead) -> list[str]:
        out = weld(['&['], self.walk(la.exp))
        out = weld(out, [']'])
        return out

    def walk_negative_lookahead(self, la: grammars.NegativeLookahead) -> list[str]:
        out = weld(['!['], self.walk(la.exp))
        out = weld(out, [']'])
        return out

    def walk_void(self, v: grammars.Void) -> list[str]:
        return [" ∅ "]

    def walk_cut(self, cut: grammars.Cut) -> list[str]:
        return [" ✂ "]

    def walk_fail(self, v) -> list[str]:
        return [" ⚠ "]

    def walk_override(self, override: grammars.Override) -> list[str]:
        out = weld([' @:('], self.walk(override.exp))
        out = weld(out, [')'])
        return out

    def walk_constant(self, constant: grammars.Constant) -> list[str]:
        return [f'`{constant.literal}`']
