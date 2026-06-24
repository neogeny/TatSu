# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from functools import cached_property
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from .base import Leaf
from .math import ffset


EOF_SYM = '$'
EOL_SYM = '⏎'


@nodedataclass
class Dot(Leaf):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.dot()

    def _pretty(self, lean=False):
        _ = lean
        return '/./'

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {('.',)}


@nodedataclass
class Fail(Leaf):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.fail()

    def _pretty(self, lean=False):
        _ = lean
        return '!()'


@nodedataclass
class Comment(Leaf):
    comment: str = ''

    def _pretty(self, lean: bool = False):
        _ = lean
        return f'(* {self.comment} *)'


@nodedataclass
class EOLComment(Comment):
    def _pretty(self, lean=False):
        _ = lean
        return f'  # {self.comment}\n'


@nodedataclass
class EOF(Leaf):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        ctx.eofcheck()

    def _pretty(self, lean=False):
        _ = lean
        return '$'


@nodedataclass
class EOL(Leaf):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        ctx.eolcheck()

    @cached_property
    def _nullable(self) -> bool:
        return True

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {('$->',)}

    def _pretty(self, lean=False):
        _ = lean
        return EOL_SYM


@nodedataclass
class Token(Leaf):
    token: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.token = self.token or self.ast

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.token(self.token)

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {(self.token,)}

    def _pretty(self, lean=False):
        _ = lean
        return repr(self.token)


@nodedataclass
class Constant(Leaf):
    literal: str = ''

    def __post_init__(self):
        super().__post_init__()
        self.literal = self.literal or self.ast

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.constant(self.literal)

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {()}

    def _pretty(self, lean=False):
        _ = lean
        return f'`{self.literal!s}`'

    @cached_property
    def _nullable(self) -> bool:
        return True


@nodedataclass
class Alert(Constant):
    level: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.ast:
            self.literal = self.ast.message.literal
            self.level = len(self.ast.level)

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.alert(message=self.literal, level=self.level)

    def _pretty(self, lean=False):
        _ = lean
        return f'{"^" * self.level}{super()._pretty()}'


@nodedataclass
class Cut(Leaf):
    def __post_init__(self):
        super().__post_init__()
        self.ast = None

    def _parse(self, ctx: Ctx) -> Any:
        ctx.cut()

    def _first(self, k: int, f: dict[str, ffset]) -> ffset:
        _ = k
        _ = f
        return {()}

    def _pretty(self, lean=False):
        _ = lean
        return '~'

    @cached_property
    def _nullable(self) -> bool:
        return True
