#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from copy import copy
from dataclasses import field
from functools import cached_property
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import typename
from .model import Grammar, Model, NamedBox, Rule
from .syntax import Sequence


@nodedataclass
class RuleInclude(NamedBox):
    _rule: Rule = field(default_factory=Rule)

    def __post_init__(self):
        if not self.name and self.ast:
            assert isinstance(self.ast, str)
            self.name = self.ast
        super().__post_init__()
        assert self.name or self._rule
        if not self.name:
            self.name = self._rule.name
        assert self.name, f'{self!s}'

    @property
    def rule(self) -> Rule:
        return self._rule

    def link(self, grammar: Grammar):
        super().link(grammar)
        if isinstance(self.exp, Model):
            return
        name = self.name
        assert name and isinstance(name, str), f'{self!r} {self.name!r}'
        self.exp = grammar.rulemap[name].exp
        assert isinstance(self.exp, Model), f'{self!r}\n{self.name!r}\n{self.exp!r}'

    def __pub__(self, sunderok: bool = False):
        assert self.name or self.rule, f'{self!r} {self.name!r}'
        pub = super().__pub__(sunderok=sunderok)
        pub['name'] = self.name
        if sunderok:
            return pub  # we're being called from __getstate__ not __repr__
        pub.pop('rule', None)
        pub.pop('exp', None)
        return pub

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        assert self.name, f'{self!r} {self.name!r}'
        if self.name not in rulenames:
            return {self.name}
        return set()

    def _pretty(self, lean=False):
        return f'>{self.name}'

    def optimized(self) -> Model:
        if not self.exp:
            return super().optimized()
        new = copy(self)  # noqa: F821
        new.exp = self.exp.optimized()
        return new


@nodedataclass
class BasedRule(Rule):
    baserule: Rule = field(default_factory=Rule)
    rhs: Model = Model()

    def __post_init__(self):
        super().__post_init__()

        assert isinstance(
            self.baserule,
            Rule,
        ), f'{typename(self.base)}: {self.baserule=!r}'

        self.params = self.params or self.baserule.params
        self.kwparams = self.kwparams or self.baserule.kwparams

        self.rhs = Sequence(ast=[self.baserule.exp, self.exp])

    def _parse(self, ctx: Ctx) -> Any:
        return self._parse_rhs(ctx, self.rhs)

    @cached_property
    def defines_single(self) -> list[str]:
        return list(set(super().defines_single) | set(self.exp.defines_single))

    @cached_property
    def defines_list(self) -> list[str]:
        return list(set(super().defines_list) | set(self.rhs.defines_list))
