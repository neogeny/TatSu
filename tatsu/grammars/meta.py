# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from ..contexts import Ctx
from .model import Model


class NameMeta(Model):
    def _parse(self, ctx: Ctx) -> Any:
        return ctx.name()

    def _pretty(self) -> str:
        return '@name'
