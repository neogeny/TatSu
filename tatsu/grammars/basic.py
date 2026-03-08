# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ._core import Model
from .math import ffset


@nodedataclass
class Dot(Model):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.dot()

    def _pretty(self, lean=False):
        return '/./'

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        return {('.',)}


@nodedataclass
class Fail(Model):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.fail()

    def _pretty(self, lean=False):
        return '!()'


@nodedataclass
class Comment(Model):
    comment: str = ''

    def _pretty(self, lean: bool = False):
        return f'(* {self.comment} *)'


@nodedataclass
class EOLComment(Comment):
    def _pretty(self, lean=False):
        return f'  # {self.comment}\n'


@nodedataclass
class EOF(Model):
    def _parse(self, ctx: Ctx) -> Any:
        ctx.eofcheck()

    def _pretty(self, lean=False):
        return '$'


@nodedataclass
class Token(Model):
    token: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.token = self.token or self.ast

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.token(self.token)

    def _first(self, k, f) -> ffset:
        return {(self.token,)}

    def _pretty(self, lean=False):
        return repr(self.token)


@nodedataclass
class Constant(Model):
    literal: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.literal = self.literal or self.ast

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.constant(self.literal)

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return f'`{self.literal!r}`'

    def _nullable(self) -> bool:
        return True


@nodedataclass
class Alert(Constant):
    level: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.literal = self.ast.message.literal
        self.level = len(self.ast.level)

    def _pretty(self, lean=False):
        return f'{"^" * self.level}{super()._pretty()}'


@nodedataclass
class Cut(Model):
    def _parse(self, ctx: Ctx) -> Any:
        ctx.cut()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '~'

    def _nullable(self) -> bool:
        return True
