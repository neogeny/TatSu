# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from os import linesep

LS_LEN = len(linesep)

def take_non_newline_whitespace_len(text: str, start: int = 0) -> int:
    if start >= len(text):
        return 0

    i = start
    while i < len(text):
        c = text[i]
        # beware of multi-character os.linesep
        if  not c.isspace() or text.startswith(linesep, i):
            break
        i += 1

    return i - start

def take_linebreak_len(text: str, start: int = 0) -> int | None:
    """Matches a whitespace-only line or EOT without slicing."""
    n = len(text)
    if start >= n:
        return 0

    newline_pos = text.find(linesep, start)
    # The segment to check is from start to newline_pos (exclusive) or to end of text
    end_of_line = newline_pos if newline_pos != -1 else n

    # Efficiency: use a loop to avoid slicing/copying
    for i in range(start, end_of_line):
        if not text[i].isspace():
            return None

    if newline_pos != -1:
        return newline_pos - start + LS_LEN
    return n - start


def take_blankline_len(text: str, start: int = 0) -> int | None:
    """Matches two consecutive whitespace-only lines."""
    off1 = take_linebreak_len(text, start)
    if off1 is None:
        return None

    off2 = take_linebreak_len(text, start + off1)
    if off2 is None:
        return None

    return off1 + off2


def indent_len(text: str, start: int = 0) -> int | None:
    """Returns the length of the leading whitespace of the line at `start`.
    Returns None if the line is empty or contains only whitespace (including the newline).
    """
    n = len(text)
    if start >= n:
        return None

    newline_pos = text.find(linesep, start)
    # Original behavior included the newline in the lstrip() check, so we search up to it
    search_limit = newline_pos + LS_LEN if newline_pos != -1 else n

    for i in range(start, search_limit):
        if not text[i].isspace():
            return i - start

    return None


def take_indent_len(text: str, start: int = 0) -> int | None:
    """Matches a line break followed by an indented line."""
    offset = take_linebreak_len(text, start)
    if offset is None:
        return None

    indent = indent_len(text, start + offset)
    if indent is None:
        return None

    return offset + indent


def take_dedent_len(text: str, pos: int = 0) -> int | None:
    """Matches a line break that returns to the zero-margin."""
    offset = take_linebreak_len(text, pos)
    if offset is None:
        return None

    # Matches if the next line has content starting at the zero margin
    if indent_len(text, pos + offset) == 0:
        return offset
    return None
