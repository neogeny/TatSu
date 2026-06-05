#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

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
    rule: Rule = field(default_factory=Rule)

    def __post_init__(self):
        super().__post_init__()
        if not self.name:
            self.name = self.rule.name

    def _set_grammar(self, grammar: Grammar):
        super()._set_grammar(grammar)
        if isinstance(self.exp, Model):
            return
        name = self.name or self.rule.name or self.exp
        assert name and isinstance(name, str), f'{self!r} {self.name!r}'
        self.exp = grammar.rulemap[name].exp
        assert isinstance(self.exp, Model), f'{self!r} {self.name!r}'

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
        assert self.name or self.rule, f'{self!r} {self.name!r}'
        # if self.name not in rulenames:
        #     return {self.name}
        return set()

    def _pretty(self, lean=False):
        return f'>{self.rule.name}'

    def optimized(self) -> Model:
        if self.exp:
            return self.exp.optimized()
        return self


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
