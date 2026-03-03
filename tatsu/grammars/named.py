# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import field

from ..ast import AST
from ..objectmodel import tatsudataclass
from ..util import typename
from .syntax import Decorator


@tatsudataclass
class Named(Decorator):
    name: str = field(default='')

    def __post_init__(self):
        if not self.ast:
            self.ast = AST(name=self.name, exp=self.exp)
        super().__post_init__()
        if not self.name:
            raise TypeError(f'{typename(self)}.name is required')
        assert getattr(self, 'name', None) is not None

    def _parse(self, ctx):
        value = self.exp._parse(ctx)
        ctx.ast[self.name] = value
        return value

    def defines(self):
        return [(self.name, False), *super().defines()]

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}:{self.exp._pretty(lean=lean)}'


@tatsudataclass
class NamedList(Named):
    def _parse(self, ctx):
        value = self.exp._parse(ctx)
        ctx.ast._setlist(self.name, value)
        return value

    def defines(self):
        return [(self.name, True), *super().defines()]

    def _pretty(self, lean=False):
        if lean:
            return self.exp._pretty(lean=True)
        return f'{self.name}+:{self.exp._pretty(lean=lean)!s}'


@tatsudataclass
class Override(Named):
    def __post_init__(self):
        # HACK:
        #   The rule for override in the bootstrap grammar uses `@:term`.
        #   That's too difficult to change... So we path conformance with Named!
        #   BaseNode.__post_init__() transfers AST entries to attributes

        self.ast = AST(name='@', exp=self.ast)
        super().__post_init__()

    def defines(self):
        return self.exp.defines()


@tatsudataclass
class OverrideList(NamedList):
    def __post_init__(self):
        self.ast = AST(name='@', exp=self.ast)
        super().__post_init__()

    def defines(self):
        return self.exp.defines()
