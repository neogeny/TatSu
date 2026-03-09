#  Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
#  SPDX-License-Identifier: BSD-4-Clause
#

# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ..ast import AST
from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import typename
from ._core import Box, NamedBox


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

    def defines(self):
        return [(self.name, False), *super().defines()]

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}:{self.exp._pretty(lean=lean)}'


@nodedataclass
class NamedList(Named):
    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        ctx.ast._setlist(self.name, value)
        return value

    def defines(self):
        return [(self.name, True), *super().defines()]

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}+:{self.exp._pretty(lean=lean)!s}'


@nodedataclass
class Override(Box):
    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        ctx.ast['@'] = value
        return value

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'@:{self.exp._pretty(lean=lean)!s}'


@nodedataclass
class OverrideList(Box):
    def _parse(self, ctx: Ctx) -> Any:
        value = self.exp._parse(ctx)
        ctx.ast._setlist('@', value)
        return value

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'@+:{self.exp._pretty(lean=lean)!s}'
