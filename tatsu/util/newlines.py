# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def take_linebreak_len(text: str, start: int = 0) -> int | None:
    """Matches a whitespace-only line or EOT without slicing."""
    if start >= len(text):
        return 0
    text = text[start:]

    lines = text.splitlines(True)
    first = lines[0]
    if not first.strip():
        return len(first)
    return None


def take_blankline_len(text: str, start: int = 0) -> int | None:
    text = text[start:]
    if not text:
        return 0
    if (off1 := take_linebreak_len(text)) is None:
        return None

    text = text[off1:]
    if not text:
        return off1

    if (off2 := take_linebreak_len(text)) is None:
        return None
    return off1 + off2


def indent_len(text: str, start: int = 0) -> int | None:
    text = text[start:].splitlines(True)[0]
    print('TEXT:', repr(text))
    if (stripped_len := len(text.lstrip())) == 0:
        return None  # an empty line
    return len(text) - stripped_len


def take_indent_len(text: str, start: int = 0) -> int | None:
    offset = take_linebreak_len(text, start)
    if offset is None:
        return None

    return offset + indent_len(text[start + offset:])


def take_dedent_len(text: str, pos: int = 0) -> int | None:
    """Matches a line break that returns to the zero-margin."""
    offset = take_linebreak_len(text, pos)
    if offset is None:
        return None

    return offset if indent_len(text, offset) == 0 else None
