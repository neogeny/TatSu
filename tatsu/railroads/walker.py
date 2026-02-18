# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from tatsu import grammars
from .railmath import (assert_one_length, ETX, lay_out, loop, RailTracks, stopnloop, weld)
from ..util.abctools import join_lists
from ..util.string import regexp, unicode_display_len as ulen
from ..walkers import NodeWalker


def tracks(model: grammars.Grammar):
    walker = RailroadNodeWalker()
    return walker.walk(model)


def draw(model: grammars.Grammar):
    for line in tracks(model):
        print(line.rstrip())


class RailroadNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    def walk(self, node: Any, *args, **kwargs) -> Any:
        return list(super().walk(node))

    def walk_default(self, node: grammars.Model) -> RailTracks:
        return [f' <{node!r}> ']

    def walk_decorator(self, decorator: grammars.Decorator) -> RailTracks:
        return self.walk(decorator.exp)

    def walk_grammar(self, grammar: grammars.Grammar) -> RailTracks:
        return join_lists(*(self.walk(r) for r in grammar.rules))

    def walk_rule(self, rule: grammars.Rule) -> RailTracks:
        out = [f'{rule.name} ●─']
        out = weld(out, self.walk(rule.exp))
        if ETX not in out:
            out = weld(out, ['─■'])
        out += [' ' * ulen(out[0])]
        return assert_one_length(out)

    def walk_optional(self, optional: grammars.Optional) -> RailTracks:
        # return lay_out([self.walk(optional.exp), ['→']])
        out = weld(['→'], self.walk(optional.exp))
        return lay_out([out, ['→']])

    def walk_closure(self, closure: grammars.Closure) -> RailTracks:
        return loop(self.walk_decorator(closure))

    def walk_positive_closure(self, closure: grammars.Closure) -> RailTracks:
        return stopnloop(self.walk_decorator(closure))

    def walk_join(self, join: grammars.Join) -> RailTracks:
        sep = weld(self.walk(join.sep), [' ✂ ─'])
        out = weld(sep, self.walk(join.exp))
        return loop(out)

    def walk_positive_join(self, join: grammars.PositiveJoin) -> RailTracks:
        sep = weld(self.walk(join.sep), [' ✂ ─'])
        out = weld(sep, self.walk(join.exp))
        return stopnloop(out)

    def walk_choice(self, choice: grammars.Choice) -> RailTracks:
        return lay_out([self.walk(o) for o in choice.options])

    def walk_option(self, option: grammars.Option) -> RailTracks:
        return self.walk(option.exp)

    def walk_sequence(self, s: grammars.Sequence) -> RailTracks:
        out = []
        for element in s.sequence:
            out = weld(out, self.walk(element))
        return assert_one_length(out)

    def walk_call(self, call: grammars.Call) -> RailTracks:
        return [f"{call.name}"]

    def walk_pattern(self, pattern: grammars.Pattern) -> RailTracks:
        pat = regexp(pattern.pattern).replace("r'", "").rstrip("'")
        return [f"/{pat}/─"]

    def walk_token(self, token: grammars.Token) -> RailTracks:
        return [f"{token.token!r}"]

    def walk_eof(self, eof: grammars.EOF) -> RailTracks:
        return [f"⇥ {ETX} "]

    def walk_lookahead(self, la: grammars.Lookahead) -> RailTracks:
        out = weld(['─ &['], self.walk(la.exp))
        out = weld(out, [']'])
        return out

    def walk_negative_lookahead(self, la: grammars.NegativeLookahead) -> RailTracks:
        out = weld(['─ !['], self.walk(la.exp))
        out = weld(out, [']'])
        return out

    def walk_void(self, v: grammars.Void) -> RailTracks:
        return [" ∅ "]

    def walk_cut(self, cut: grammars.Cut) -> RailTracks:
        return [" ✂ ─"]

    def walk_fail(self, v) -> RailTracks:
        return [" ⚠ "]

    def walk_override(self, override: grammars.Override) -> RailTracks:
        out = weld([' @:('], self.walk(override.exp))
        out = weld(out, [')'])
        return out

    def walk_override_list(self, override: grammars.OverrideList):
        out = weld([' @+:('], self.walk(override.exp))
        out = weld(out, [')'])
        return out

    def walk_constant(self, constant: grammars.Constant) -> RailTracks:
        return [f'`{constant.literal}`']

    def walk_dot(self, dot: grammars.Dot):
        return [" ∀ "]

    def walk_group(self, group: grammars.Group):
        return self.walk_decorator(group)

    def walk_alert(self, alert: grammars.Alert):
        return [f'{'^' * alert.level}`{alert.literal}`']

    def walk_skip_to(self, skipto: grammars.SkipTo):
        out = weld([' ->('], self.walk(skipto.exp))
        out = weld(out, [')'])
        return out

    def walk_rule_include(self, include: grammars.RuleInclude):
        out = weld([' >('], self.walk(include.rule.name))
        out = weld(out, [')'])
        return out

    def walk_based_rule(self, rule: grammars.BasedRule):
        out = [f'{rule.name} < {rule.baserule}●─']
        out = weld(out, self.walk(rule.rhs))
        if ETX not in out:
            out = weld(out, ['─■'])
        out += [' ' * ulen(out[0])]
        return assert_one_length(out)
