# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from tatsu import grammars

from ..util.abctools import join_lists
from ..util.string import regexp
from ..util.string import unicode_display_len as ulen
from ..walkers import NodeWalker
from .railmath import ETX, Rails, assert_one_length, lay_out, loop, stopnloop, weld


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

    def walk_default(self, node: grammars.Model) -> Rails:
        return [f' <{node!r}> ']

    def walk_decorator(self, decorator: grammars.Decorator) -> Rails:
        return self.walk(decorator.exp)

    def walk_grammar(self, grammar: grammars.Grammar) -> Rails:
        return join_lists(*(self.walk(r) for r in grammar.rules))

    def walk_rule(self, rule: grammars.Rule) -> Rails:
        decorators = ''
        if rule.decorators:
            decorators = ' '.join(f'@{d}' for d in rule.decorators) + ' '

        params = ''
        if rule.params:
            params = '∷' + ','.join(p for p in rule.params)
        if rule.kwparams:
            params = ',' + ','.join(f'{k}={v}' for k, v in rule.kwparams.items())

        leftrec = ''
        if rule.is_leftrec:
            leftrec = '⟳'
        elif not rule.is_memoizable:
            leftrec = '⊬'

        base = ''
        if rule.base:
            base = f"≤({rule.base})"

        out = [f'{decorators}{leftrec}{rule.name}{base}{params} ●─']
        out = weld(out, self.walk(rule.exp))
        if ETX not in out:
            out = weld(out, ['─■'])
        out += [' ' * ulen(out[0])]
        return assert_one_length(out)

    def walk_optional(self, optional: grammars.Optional) -> Rails:
        # return lay_out([self.walk(optional.exp), ['→']])
        out = weld(['→'], self.walk(optional.exp))
        return lay_out([out, ['→']])

    def walk_closure(self, closure: grammars.Closure) -> Rails:
        return loop(self.walk_decorator(closure))

    def walk_positive_closure(self, closure: grammars.Closure) -> Rails:
        return stopnloop(self.walk_decorator(closure))

    def walk_join(self, join: grammars.Join) -> Rails:
        sep = weld(self.walk(join.sep), [' ✂ ─'])
        out = weld(sep, self.walk(join.exp))
        return loop(out)

    def walk_positive_join(self, join: grammars.PositiveJoin) -> Rails:
        sep = weld(self.walk(join.sep), [' ✂ ─'])
        out = weld(sep, self.walk(join.exp))
        return stopnloop(out)

    def walk_choice(self, choice: grammars.Choice) -> Rails:
        return lay_out([self.walk(o) for o in choice.options])

    def walk_option(self, option: grammars.Option) -> Rails:
        return self.walk(option.exp)

    def walk_sequence(self, s: grammars.Sequence) -> Rails:
        out = []
        for element in s.sequence:
            out = weld(out, self.walk(element))
        return assert_one_length(out)

    def walk_call(self, call: grammars.Call) -> Rails:
        return [f"{call.name}"]

    def walk_pattern(self, pattern: grammars.Pattern) -> Rails:
        pat = regexp(pattern.pattern).replace("r'", "").rstrip("'")
        return [f"/{pat}/─"]

    def walk_token(self, token: grammars.Token) -> Rails:
        return [f"{token.token!r}"]

    def walk_eof(self, eof: grammars.EOF) -> Rails:
        return [f"⇥ {ETX} "]

    def walk_lookahead(self, la: grammars.Lookahead) -> Rails:
        out = weld(['─ &['], self.walk(la.exp))
        out = weld(out, [']'])
        return out

    def walk_negative_lookahead(self, la: grammars.NegativeLookahead) -> Rails:
        out = weld(['─ !['], self.walk(la.exp))
        out = weld(out, [']'])
        return out

    def walk_void(self, v: grammars.Void) -> Rails:
        return [" ∅ "]

    def walk_cut(self, cut: grammars.Cut) -> Rails:
        return [" ✂ ─"]

    def walk_fail(self, v) -> Rails:
        return [" ⚠ "]

    def walk_constant(self, constant: grammars.Constant) -> Rails:
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
        out = [f' >({include.rule.name}) ']
        return out

    def walk_based_rule(self, rule: grammars.BasedRule):
        out = [f'{rule.name} < {rule.baserule}●─']
        out = weld(out, self.walk(rule.rhs))
        if ETX not in out:
            out = weld(out, ['─■'])
        out += [' ' * ulen(out[0])]
        return assert_one_length(out)

    def walk_named(self, named: grammars.Named) -> Rails:
        out = weld([f' [{named.name}]('], self.walk(named.exp))
        out = weld(out, [')'])
        return out

    def walk_named_list(self, named: grammars.NamedList) -> Rails:
        out = weld([f' [`{named.name}`]+('], self.walk(named.exp))
        out = weld(out, [')'])
        return out

    def walk_override(self, override: grammars.Override) -> Rails:
        out = weld([' @('], self.walk(override.exp))
        out = weld(out, [')'])
        return out

    def walk_override_list(self, override: grammars.OverrideList):
        out = weld([' @+('], self.walk(override.exp))
        out = weld(out, [')'])
        return out
