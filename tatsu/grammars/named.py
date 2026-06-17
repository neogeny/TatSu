#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from functools import cached_property
from typing import Any

from ..contexts import _AT_, AST, Ctx
from ..objectmodel import nodedataclass
from ..util import typename
from .base import Box, NamedBox


@nodedataclass
class Named(NamedBox):
    def __post_init__(self):
        if not self.ast:
            self.ast = AST(name=self.name, exp=self.exp)
        super().__post_init__()
        if not self.name:
            raise TypeError(f"{typename(self)} is missing required: 'name'")
        assert getattr(self, 'name', None) is not None

    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        ctx.ast[self.name] = value
        return value

    @cached_property
    def defines_single(self) -> list[str]:
        return list({self.name, *super().defines_single})

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}={self.exp._pretty(lean=lean)}'


@nodedataclass
class NamedList(Named):
    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        ctx.ast._setlist(self.name, value)
        return value

    @cached_property
    def defines_list(self) -> list[str]:
        return list({self.name, *super().defines_list})

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}+={self.exp._pretty(lean=lean)!s}'


@nodedataclass
class Override(Box):
    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        ctx.ast[_AT_] = value
        return {_AT_: value}

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'={self.exp._pretty(lean=lean)!s}'


@nodedataclass
class OverrideList(Box):
    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        if _AT_ not in ctx.ast:
            value = [value]
        ctx.ast[_AT_] = value
        return {_AT_: value}

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'+={self.exp._pretty(lean=lean)!s}'
