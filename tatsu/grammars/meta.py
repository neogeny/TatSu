# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ..contexts import Ctx
from .model import Model


class Meta(Model):
    pass


class NameMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchname()

    def _pretty(self, lean: bool = False) -> str:
        return '@name'


class IntMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchint()

    def _pretty(self, lean: bool = False) -> str:
        return '@int'


class UIntMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchuint()

    def _pretty(self, lean: bool = False) -> str:
        return '@uint'


class FloatMeta(Meta):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.matchfloat()

    def _pretty(self, lean: bool = False) -> str:
        return '@float'
