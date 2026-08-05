# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re
from functools import cached_property
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import regex_source, regexpp
from .base import Leaf
from .math import ffset


@nodedataclass
class Pattern(Leaf):
    pattern: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.pattern = self.pattern or self.ast or ""
        try:
            self._regex = re.compile(self.pattern)
        except Exception as e:
            raise ValueError(f"Invalid regex pattern: {self.pattern!r}") from e

    def _parse(self, ctx: Ctx) -> Any:
        return ctx.pattern(self.pattern or r'\\')

    def _first(self, k, f) -> ffset:
        _ = k, f
        x = str(self)
        if bool(self._regex.match('')):
            return {(), (x,)}
        else:
            return {(x,)}

    def _pretty(self, lean=False):
        _ = lean
        return regex_source(self.pattern or "")

    @cached_property
    def _nullable(self) -> bool:
        return bool(self._regex.match(''))

    def __str__(self) -> str:
        return regexpp(self.pattern)[2:-1]
