# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ..contexts import Ctx
from .base import Leaf


class Meta(Leaf):
    pass


class NameMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchname()

    def _pretty(self, lean: bool = False) -> str:
        _ = lean
        return '@name'


class IntMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchint()

    def _pretty(self, lean: bool = False) -> str:
        _ = lean
        return '@int'


class UIntMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchuint()

    def _pretty(self, lean: bool = False) -> str:
        _ = lean
        return '@uint'


class FloatMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchfloat()

    def _pretty(self, lean: bool = False) -> str:
        _ = lean
        return '@float'


class BoolMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchbool()

    def _pretty(self, lean: bool = False) -> str:
        _ = lean
        return '@bool'
