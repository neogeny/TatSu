#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field

from ..contexts import ParseContext
from ..objectmodel import tatsudataclass
from ..util import typename
from ._core import Box, Model, Result, Rule
from .syntax import Sequence


@tatsudataclass
class RuleInclude(Box):
    rule: Rule = field(default_factory=Rule)

    def __post_init__(self):
        super().__post_init__()
        assert isinstance(self.rule, Rule)
        # note: self.ast: str is the rule name
        self.exp = self.rule.exp

    def _pretty(self, lean=False):
        return f'>{self.rule.name}'


@tatsudataclass
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

    def _parse(self, ctx: ParseContext) -> Result:
        return self._parse_rhs(ctx, self.rhs)

    def defines(self):
        return super().defines() + self.rhs.defines()
