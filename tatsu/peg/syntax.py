# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from copy import copy
from dataclasses import field
from functools import cached_property
from typing import Any, Self, cast

from ..contexts import AST, Ctx
from ..contexts.cst import cstmerge
from ..exceptions import FailedParse, FailedRef
from ..objectmodel import nodedataclass
from ..util import indent, trim, typename
from .base import PEP8_LLEN, Box, Leaf, Model, Rule
from .math import ffset, kdot, ref


@nodedataclass
class Group(Box):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.groupexp(self.exp._parse)

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'({trim(exp)})'
        return f'(\n{indent(exp)}\n)'

    def optimized(self) -> Model:
        newexp = self.exp.optimized()
        assert isinstance(newexp, Model)

        if isinstance(newexp, Leaf | Group):
            return newexp
        return Group(newexp)


@nodedataclass
class SkipGroup(Box):
    def _parse(self, ctx: Ctx) -> Any:
        with ctx.skipgroup():
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
            return self.exp._parse(ctx)

    def _pretty(self, lean=False):
        return '&' + self.exp._pretty(lean=lean)

    @cached_property
    def _nullable(self) -> bool:
        return True


@nodedataclass
class NegativeLookahead(Box):
    def _parse(self, ctx: Ctx) -> Any:
        with ctx.ifnot_():
            return self.exp._parse(ctx)

    def _pretty(self, lean=False):
        return '!' + str(self.exp._pretty(lean=lean))

    @cached_property
    def _nullable(self) -> bool:
        return True


@nodedataclass
class SkipTo(Box):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.skip_to(self.exp._parse)

    def _first(self, k, f) -> ffset:
        return {('.',)} | super()._first(k, f)

    def _pretty(self, lean=False):
        return '->' + self.exp._pretty(lean=lean)


@nodedataclass
class Optional(Box):
    def _parse(self, ctx: Ctx) -> Any:
        ctx.states.push()
        try:
            self._add_defined(ctx)
            value = self.exp._parse(ctx)
            ctx.states.merge()
            return value
        except FailedParse:
            if ctx.states.undo().cutseen:
                raise
            return None

    def _first(self, k, f) -> ffset:
        return {()} | self.exp._first(k, f)

    def _pretty(self, lean=False):
        exp = self.exp._pretty(lean=lean)
        if len(exp.splitlines()) <= 1:
            return f'[{exp}]'
        return f'[\n{exp}\n]'

    @cached_property
    def _nullable(self) -> bool:
        return True

    def optimized(self) -> Self | Model:
        from .closure import Closure, Gather, Join

        exp = self.exp.optimized()
        if isinstance(
            exp, Optional | Closure | Join | Gather
        ) and 'Positive' not in typename(exp):
            return exp
        new = copy(self)
        new.exp = exp
        return new


@nodedataclass
class Sequence(Model):
    sequence: list[Model] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if not self.sequence:
            self.sequence = list(self.ast or [])
        assert isinstance(self.sequence, list), self.sequence

    def _parse(self, ctx: Ctx) -> Any:
        self._add_defined(ctx)
        out = None
        for s in self.sequence:
            exp = s
            while isinstance(exp, Group):
                exp = exp.exp

            r = exp._parse(ctx)
            if r is None:
                continue

            out = cstmerge(out, r)
        return out

    @cached_property
    def defines_single(self) -> list[str]:
        return list(set().union(*(s.defines_single for s in self.sequence)))

    @cached_property
    def defines_list(self) -> list[str]:
        return list(set().union(*(s.defines_list for s in self.sequence)))

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        return set().union(*(s.missing_rules(rulenames) for s in self.sequence))

    def _used_rule_names(self):
        return set().union(*(s._used_rule_names() for s in self.sequence))

    def _first(self, k, f) -> ffset:
        result: ffset = {()}
        for s in self.sequence:
            assert isinstance(s, Model), f'{type(s)}:{s} is not a Model'
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

    @cached_property
    def _nullable(self) -> bool:
        return all(s._nullable for s in self.sequence)

    def optimized(self) -> Model | Self:
        seq = [e.optimized() if isinstance(e, Model) else e for e in self.sequence]
        for s in seq:
            assert isinstance(s, Model)
        if len(seq) == 1 and isinstance(seq[0], Model):
            return seq[0]
        # NOTE a new Sequence will not have left recursion attributes set
        new = copy(self)
        new.sequence = seq
        return new


@nodedataclass
class Call(Leaf):
    name: str = ''
    _rule: Rule | None = None

    def __post_init__(self):
        if not self.name:
            self.ast = AST(name=self.ast)
        super().__post_init__()
        assert isinstance(self.name, str), self.name

    @property
    def rule(self) -> Rule | None:
        return self._rule

    def follow_ref(self) -> Model:
        return self.grammar.rulemap.get(self.name, self)

    def _parse(self, ctx: Ctx) -> Any:
        try:
            if self._rule:
                return ctx.expcall(self._rule._parse)
            parse = ctx.find_rule(self.name)
            return ctx.expcall(parse)
        except KeyError as e:
            raise ctx.newexcept(self.name, excls=FailedRef) from e

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        if self.name not in rulenames:
            return {self.name}
        return set()

    def _used_rule_names(self) -> set[str]:
        return {self.name}

    def _first(self, k, f) -> ffset:
        _ = k
        return f[self.name] | {ref(self.name)}

    def _follow(self, k, fl, a):
        _ = k
        fl[self.name] |= a
        return set(a) | {self.name}

    def _pretty(self, lean=False):
        _ = lean
        return self.name

    def is_nullable(self) -> bool:
        return self.grammar.rulemap[self.name]._nullable

    def optimized(self) -> Call:
        if not self._rule or not isinstance(self._rule.exp, Call):
            return self

        rule = cast(Rule, self._rule)
        assert rule is not None
        while isinstance(rule.exp, Call):
            call = rule.exp
            if not call._rule:
                break
            rule = call._rule
        new = Call(
            name=rule.name,
        )
        new._rule = rule
        return new

    def __str__(self):
        return str(ref(self.name))
