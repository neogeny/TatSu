# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import override

from tatsu import grammars
from .railmath import assert_one_width, concatenate, loop, merge, positive_loop
from ..util.abctools import join_lists
from ..util.string import unicode_display_len as ulen
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

    def walk_rule(self, rule: grammars.Rule) -> list[str]:
        out = [f'{rule.name} ●─']
        out = concatenate(out, self.walk(rule.exp))
        out = concatenate(out, ['■'])
        out += [' ' * ulen(out[0])]
        return assert_one_width(out)

    # def walk_optional(self, o) -> list[str]:
    #     return ['']  # to be implemented
    #
    def walk_closure(self, closure: grammars.Closure) -> list[str]:
        return loop(self.walk_decorator(closure))

    def walk_positive_closure(self, closure: grammars.Closure) -> list[str]:
        return positive_loop(self.walk_decorator(closure))

    def walk_choice(self, choice: grammars.Choice) -> list[str]:
        return merge([self.walk(o) for o in choice.options])

    def walk_option(self, option: grammars.Option) -> list[str]:
        return self.walk(option.exp)

    def walk_sequence(self, s: grammars.Sequence) -> list[str]:
        out = []
        for element in s.sequence:
            out = concatenate(out, self.walk(element))
        return assert_one_width(out)

    def walk_call(self, call: grammars.Call) -> list[str]:
        return [f"{call.name}"]

    def walk_pattern(self, pattern: grammars.Pattern) -> list[str]:
        return [pattern.pattern]  # to be implemented

    def walk_token(self, token: grammars.Token) -> list[str]:
        return [f"{token.token!r}"]

    def walk_eof(self, eof: grammars.EOF) -> list[str]:
        return ["🔚 "]

    def walk_lookahead(self, la: grammars.Lookahead) -> list[str]:
        out = concatenate(['&['], self.walk(la.exp))
        out = concatenate(out, [']'])
        return out

    def walk_negative_lookahead(self, la: grammars.NegativeLookahead) -> list[str]:
        out = concatenate(['!['], self.walk(la.exp))
        out = concatenate(out, [']'])
        return out

    def walk_void(self, v: grammars.Void) -> list[str]:
        return [" ∅ "]

    def walk_cut(self, cut: grammars.Cut) -> list[str]:
        return [" ✂ "]

    def walk_fail(self, v) -> list[str]:
        return [" ⚠ "]

    # def walk_endrule(self, ast) -> list[str]:
    #     return ['']  # to be implemented
    #
    # def walk_emptyline(self, ast, *args) -> list[str]:
    #     return ['']  # to be implemented

    def walk_override(self, override: grammars.Override) -> list[str]:
        out = concatenate([' @:('], self.walk(override.exp))
        out = concatenate(out, [')'])
        return out

    def walk_constant(self, constant: grammars.Constant) -> list[str]:
        return [f'`{constant.literal}`']
