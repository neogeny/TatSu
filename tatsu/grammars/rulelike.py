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
from ..exceptions import FailedUnlinkedRule
from ..objectmodel import nodedataclass
from ..util import typename
from .base import Grammar, Leaf, Model, Rule
from .syntax import Sequence


@nodedataclass
class RuleInclude(Leaf):
    name: str = field(default='')  # type: ignore
    _exp: Model | None = None

    def __post_init__(self):
        if not self.name and self.ast:
            assert isinstance(self.ast, str)
            self.name = self.ast
        super().__post_init__()
        assert self.name, f'{self!s}'

    def _parse(self, ctx: Ctx) -> Any:
        if self._exp is None:
            raise ctx.newexcept(f'Unlinked rule {self.name!r}', FailedUnlinkedRule)
        return self._exp._parse(ctx)

    @property
    def exp(self) -> Model | None:
        return self._exp

    def link(self, grammar: Grammar) -> None:
        super().link(grammar)
        name = self.name
        assert name and isinstance(name, str), f'{self!r} {self.name!r}'
        self._exp = grammar.rulemap[name].exp
        assert isinstance(self._exp, Model), f'{self!r}\n{self.name!r}\n{self._exp!r}'

    def missing_rules(self, rulenames: set[str]) -> set[str]:
        assert self.name, f'{self!r} {self.name!r}'
        if self.name not in rulenames:
            return {self.name}
        return set()

    def _pretty(self, lean=False):
        return f'>{self.name}'

    @cached_property
    def defines_single(self) -> list[str]:
        if not self.exp:
            return []
        return self.exp.defines_single

    @cached_property
    def defines_list(self) -> list[str]:
        if not self.exp:
            return []
        return self.exp.defines_list

    def optimized(self) -> Model:
        if not self.exp:
            return super().optimized()
        new = copy(self)  # noqa: F821
        new._exp = self.exp.optimized()
        return new

    # def __pub__(self, sunderok: bool = False) -> dict[str, Any]:
    #     pub = super().__pub__(sunderok)
    #     if sunderok:
    #         pub['exp'] = self.exp
    #     return pub


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
