# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses as dc
import re

from ..objectmodel import tatsudataclass
from ._core import Model
from .math import ffset


@tatsudataclass
class Pattern(Model):
    pattern: str | None = None
    _patterns: list[str] = dc.field(init=False, default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self._patterns = self.ast if isinstance(self.ast, list) else [self.ast]
        if self.pattern is None:
            self.pattern = ''.join(self._patterns or [])
        else:
            self._patterns = self.pattern.splitlines()
        self._regex = re.compile(self.pattern)

    def _parse(self, ctx):
        return ctx._pattern(self.pattern or r'\\')

    def _first(self, k, f) -> ffset:
        x = str(self)
        if bool(self._regex.match('')):
            return {(), (x,)}
        else:
            return {(x,)}

    def _pretty(self, lean=False):
        parts = []
        for pat in (str(p) for p in self._patterns):
            if '/' in pat:
                newpat = pat.replace('"', r'\"')
                regex = f'?"{newpat}"'
            else:
                regex = f'/{pat}/'
            parts.append(regex)
        return ' + '.join(parts)

    def _nullable(self) -> bool:
        return bool(self._regex.match(''))
