# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field
from itertools import takewhile
from typing import Any

from ..contexts import AST, Ctx, Func
from ..exceptions import FailedRef
from ..objectmodel import nodedataclass
from ..util import indent, safe_name, trim
from ._core import PEP8_LLEN, Box, Model
from .math import ffset, kdot, ref


@nodedataclass
class Group(Box):
    def _parse(self, ctx: Ctx) -> Any:
        with ctx.group():
            self.exp._parse(ctx)
            return ctx.last_node

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'({trim(exp)})'
        return f'(\n{indent(exp)}\n)'


@nodedataclass
class Skip(Box):
    def _parse(self, ctx: Ctx) -> Any:
        with ctx.skip():
            self.exp._parse(ctx)
            return None

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'(?:{trim(exp)})'
        return f'(?:\n{indent(exp)}\n)'


@nodedataclass
class Lookahead(Box):
    def _parse(self, ctx: Ctx) -> Any:
        with ctx.if_():
            return super()._parse(ctx)

    def _pretty(self, lean=False):
        return '&' + self.exp._pretty(lean=lean)

    def _nullable(self) -> bool:
        return True


@nodedataclass
class NegativeLookahead(Box):
    def _parse(self, ctx: Ctx) -> Any:
        with ctx.ifnot_():
            return super()._parse(ctx)

    def _pretty(self, lean=False):
        return '!' + str(self.exp._pretty(lean=lean))

    def _nullable(self) -> bool:
        return True


@nodedataclass
class SkipTo(Box):
    def _parse(self, ctx: Ctx) -> Any:
        super_parse: Func = super()._parse  # type: ignore
        return ctx.skip_to(super_parse)

    def _first(self, k, f) -> ffset:
        return {('.',)} | super()._first(k, f)

    def _pretty(self, lean=False):
        return '->' + self.exp._pretty(lean=lean)


@nodedataclass
class Optional(Box):
    def _parse(self, ctx: Ctx) -> Any:
        self._add_defined_attributes(ctx, ctx.ast)
        with ctx.optional():
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


@nodedataclass
class Sequence(Model):
    sequence: list[Model] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.sequence:
            self.sequence = list(self.ast or [])
        assert isinstance(self.sequence, list), self.sequence

    def _parse(self, ctx: Ctx) -> Any:
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


@nodedataclass
class Call(Model):
    name: str = ''

    def __post_init__(self):
        if not self.name:
            self.ast = AST(name=self.ast)
        super().__post_init__()
        self.name = safe_name(self.name)
        assert isinstance(self.name, str), self.name

    def follow_ref(self) -> Model:
        return self.grammar.rulemap.get(self.name, self)

    def _parse(self, ctx: Ctx) -> Any:
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
