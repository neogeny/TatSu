# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..objectmodel import tatsudataclass
from ._core import Model
from .math import ffset


@tatsudataclass
class Dot(Model):
    def _parse(self, ctx):
        return ctx._dot()

    def _pretty(self, lean=False):
        return '/./'

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        return {('.',)}


@tatsudataclass
class Fail(Model):
    def _parse(self, ctx):
        return ctx._fail()

    def _pretty(self, lean=False):
        return '!()'


@tatsudataclass
class Comment(Model):
    comment: str = ''

    def _pretty(self, lean: bool = False):
        return f'(* {self.comment} *)'


@tatsudataclass
class EOLComment(Comment):
    def _pretty(self, lean=False):
        return f'  # {self.comment}\n'


@tatsudataclass
class EOF(Model):
    def _parse(self, ctx):
        ctx._check_eof()

    def _pretty(self, lean=False):
        return '$'


@tatsudataclass
class Token(Model):
    token: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.token = self.token or self.ast

    def _parse(self, ctx):
        return ctx._token(self.token)

    def _first(self, k, f) -> ffset:
        return {(self.token,)}

    def _pretty(self, lean=False):
        return repr(self.token)


@tatsudataclass
class Constant(Model):
    literal: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.literal = self.literal or self.ast

    def _parse(self, ctx):
        return ctx._constant(self.literal)

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return f'`{self.literal!r}`'

    def _nullable(self) -> bool:
        return True


@tatsudataclass
class Alert(Constant):
    level: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.literal = self.ast.message.literal
        self.level = len(self.ast.level)

    def _parse(self, ctx):
        return super()._parse(ctx)

    def _pretty(self, lean=False):
        return f'{"^" * self.level}{super()._pretty()}'


@tatsudataclass
class Cut(Model):
    def _parse(self, ctx):
        ctx._cut()

    def _first(self, k, f) -> ffset:
        return {()}

    def _pretty(self, lean=False):
        return '~'

    def _nullable(self) -> bool:
        return True
