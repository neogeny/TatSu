# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Editor-friendly run-length compression for JSONL text.

Replaces runs of 5+ spaces with ``~N~`` markers, guarded so that
any natural ``~`` in the input becomes ``~~`` and round-trips
correctly. A text editor, a ``sed`` script, or ``grep`` can all
operate on the compressed form.
"""

from __future__ import annotations

import re


_COMPRESS_RE = re.compile(r"     +")

_EXPAND_RE = re.compile(r"~~|~(\d+)~")


def _compress_dispatch(m: re.Match) -> str:
    return f"~{len(m.group(0))}~"


def compress(s: str) -> str:
    s = s.replace("~", "~~")
    return _COMPRESS_RE.sub(_compress_dispatch, s)


def _expand_dispatch(m: re.Match) -> str:
    if m.group(0) == "~~":
        return "~"
    return " " * int(m.group(1))


def expand(s: str) -> str:
    return _EXPAND_RE.sub(_expand_dispatch, s)
