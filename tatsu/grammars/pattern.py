# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses as dc
import re
from typing import Any

from ..contexts import Ctx
from ..objectmodel import nodedataclass
from ..util import regexpp
from ._core import Model
from .math import ffset


@nodedataclass
class Pattern(Model):
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
        x = str(self)
        if bool(self._regex.match('')):
            return {(), (x,)}
        else:
            return {(x,)}

    def _pretty(self, lean=False):
        pat = self.pattern or ""
        if '/' in pat:
            newpat = pat.replace('"', r'\"')
            regex = f'?"{newpat}"'
        else:
            regex = f'/{pat}/'
        return regex

    def _nullable(self) -> bool:
        return bool(self._regex.match(''))

    def __str__(self) -> str:
        return regexpp(self.pattern)[2:-1]
