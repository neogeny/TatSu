#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field
from itertools import takewhile

from ..ast import AST
from ..contexts import ParseContext
from ..exceptions import FailedRef
from ..objectmodel import tatsudataclass
from ..util import indent, trim
from ._core import PEP8_LLEN, Box, Model, Result
from .math import ffset, kdot, ref


@tatsudataclass
class Group(Box):
    def _parse(self, ctx: ParseContext) -> Result:
        with ctx.group():
            self.exp._parse(ctx)
            return ctx.last_node

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'({trim(exp)})'
        return f'(\n{indent(exp)}\n)'


@tatsudataclass
class Lookahead(Box):
    def _parse(self, ctx: ParseContext) -> Result:
        with ctx.if_():
            return super()._parse(ctx)

    def _pretty(self, lean=False):
        return '&' + self.exp._pretty(lean=lean)

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class NegativeLookahead(Box):
    def _parse(self, ctx: ParseContext) -> Result:
        with ctx.ifnot_():
            return super()._parse(ctx)

    def _pretty(self, lean=False):
        return '!' + str(self.exp._pretty(lean=lean))

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class SkipTo(Box):
    def _parse(self, ctx: ParseContext) -> Result:
        super_parse = super()._parse
        return ctx._skip_to(lambda: super_parse(ctx))

    def _first(self, k, f) -> ffset:
        return {('.',)} | super()._first(k, f)

    def _pretty(self, lean=False):
        return '->' + self.exp._pretty(lean=lean)


@tatsudataclass
class Choice(Model):
    options: list[Model] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.options = self.options or self.ast
        assert isinstance(self.options, list), repr(self.options)

    def _parse(self, ctx: ParseContext) -> Result:
        with ctx.choice() as ch:
            ch.options = [lambda o=o: o._parse(ctx) for o in self.options]  # type: ignore
            ch.expecting(*self.lookaheadlist())
        return ch.result

    def defines(self):
        return [d for o in self.options for d in o.defines()]

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(*[o.missing_rules(rulenames) for o in self.options])

    def _used_rule_names(self):
        return set().union(*[o._used_rule_names() for o in self.options])

    def _first(self, k, f) -> ffset:
        result = set()
        for o in self.options:
            result |= o._first(k, f)
        self._firstset = result
        return result

    def _follow(self, k, fl, a):
        for o in self.options:
            o._follow(k, fl, a)
        return a

    def nodecount(self) -> int:
        return 1 + sum(o.nodecount() for o in self.options)

    def _pretty(self, lean=False):
        options = [str(o._pretty(lean=lean)) for o in self.options]

        multi = any(len(o.splitlines()) > 1 for o in options)
        single = ' | '.join(o for o in options)

        if multi:
            return '\n|\n'.join(indent(o) for o in options)
        elif options and len(single) > PEP8_LLEN:
            return '| ' + '\n| '.join(o for o in options)
        else:
            return single

    def _nullable(self) -> bool:
        return any(o._nullable() for o in self.options)

    def callable_at_same_pos(self) -> list[Model]:
        return self.options


@tatsudataclass
class Option(Box):
    def _parse(self, ctx: ParseContext) -> Result:
        result = super()._parse(ctx)
        self._add_defined_attributes(ctx, result)
        return result


@tatsudataclass
class Optional(Box):
    def _parse(self, ctx: ParseContext) -> Result:
        self._add_defined_attributes(ctx, ctx.ast)
        with ctx._optional():
            return self.exp._parse(ctx)

    def _first(self, k, f) -> ffset:
        return {()} | self.exp._first(k, f)

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'[{exp}]'
        return f'[\n{exp}\n]'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Sequence(Model):
    sequence: list[Model] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.sequence:
            self.sequence = self.ast or []
        assert isinstance(self.sequence, list), self.sequence

    def _parse(self, ctx: ParseContext) -> Result:
        return [s._parse(ctx) for s in self.sequence]

    def defines(self):
        return [d for s in self.sequence for d in s.defines()]

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(*[s.missing_rules(rulenames) for s in self.sequence])

    def _used_rule_names(self):
        return set().union(*[s._used_rule_names() for s in self.sequence])

    def _first(self, k, f) -> ffset:
        result: ffset = {()}
        for s in self.sequence:
            x = s._first(k, f)
            result = kdot(result, x, k)
        self._firstset = result
        return result

    def _follow(self, k, fl, a):
        fs = a
        for x in reversed(self.sequence):
            if isinstance(x, Call):
                fl[x.name] |= fs
            x._follow(k, fl, fs)
            fs = kdot(x.firstset(k=k), fs, k)
        return a

    def nodecount(self) -> int:
        return 1 + sum(s.nodecount() for s in self.sequence)

    def _pretty(self, lean=False):
        seq = [str(s._pretty(lean=lean)) for s in self.sequence]
        single = ' '.join(seq)
        if len(single) <= PEP8_LLEN and len(single.splitlines()) <= 1:
            return single
        else:
            return '\n'.join(seq)

    def _nullable(self) -> bool:
        return all(s._nullable() for s in self.sequence)

    def callable_at_same_pos(self) -> list[Model]:
        head = list(takewhile(lambda c: c.is_nullable(), self.sequence))
        if len(head) < len(self.sequence):
            head.append(self.sequence[len(head)])
        return head


@tatsudataclass
class Call(Model):
    name: str = ''

    def __post_init__(self):
        if not self.name:
            self.ast = AST(name=self.ast)
        super().__post_init__()
        assert isinstance(self.name, str), self.name

    def follow_ref(self) -> Model:
        return self.grammar.rulemap.get(self.name, self)

    def _parse(self, ctx: ParseContext) -> Result:
        try:
            rule = ctx.find_rule(self.name)
            return rule(ctx)
        except KeyError as e:
            raise ctx.newexcept(self.name, excls=FailedRef) from e

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        if self.name not in rulenames:
            return {self.name}
        return set()

    def _used_rule_names(self) -> set[str]:
        return {self.name}

    def _first(self, k, f) -> ffset:
        return f[self.name] | {ref(self.name)}

    def _follow(self, k, fl, a):
        fl[self.name] |= a
        return set(a) | {self.name}

    def _pretty(self, lean=False):
        return self.name

    def is_nullable(self) -> bool:
        return self.grammar.rulemap[self.name].is_nullable()

    def __str__(self):
        return str(ref(self.name))
