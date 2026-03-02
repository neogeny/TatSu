# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses as dc
import re

from tatsu.grammars import Model
from tatsu.grammars.math import ffset
from tatsu.objectmodel import tatsudataclass


@tatsudataclass
class Pattern(Model):
    pattern: str = ''
    patterns: list[str] = dc.field(init=False, default_factory=list)
    regex: Pattern | None = dc.field(init=False, default=None)

    def __post_init__(self):
        super().__post_init__()
        self.patterns = self.ast if isinstance(self.ast, list) else [self.ast]
        self.pattern = ''.join(self.patterns)
        self.regex = re.compile(self.pattern)

    def _parse(self, ctx):
        return ctx._pattern(self.pattern)

    def _first(self, k, f) -> ffset:
        x = str(self)
        if bool(self.regex.match('')):
            return {(), (x,)}
        else:
            return {(x,)}

    def _pretty(self, lean=False):
        parts = []
        for pat in (str(p) for p in self.patterns):
            if '/' in pat:
                newpat = pat.replace('"', r'\"')
                regex = f'?"{newpat}"'
            else:
                regex = f'/{pat}/'
            parts.append(regex)
        return ' + '.join(parts)

    def _nullable(self) -> bool:
        return bool(self.regex.match(''))

    def __str__(self):
        return self.pattern
