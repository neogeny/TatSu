# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re


def makere(wsp: str, cmt: str, eol: str) -> re.Pattern:
    pattern = rf"(?m)^(?:(?P<cmt>{cmt})|(?P<eol>{eol})|(?P<wsp>{wsp}))"
    return re.compile(pattern)


def match_iter(pattern: re.Pattern, text: str, pos: int = 0) -> int:
    """Return the next match object from text at or after position pos."""
    for match in pattern.finditer(text, pos):
        pos = match.end()
    return pos


def joinregexps(**patterns: str) -> re.Pattern:
    """Join multiple named patterns into a single regex pattern."""
    inner = "|".join(f"(?P<{name}>{pattern})" for name, pattern in patterns.items())
    pattern = f"(?m)^(?:{inner})"
    return re.compile(pattern)
