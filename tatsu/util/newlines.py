# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def empty_line(text: str, pos: int = 0) -> int | None:
    """Matches a whitespace-only line or EOT without slicing."""
    if pos >= len(text):
        return 0

    nl_pos = text.find('\n', pos)

    if nl_pos == -1:
        # Check if the remainder of the string is only whitespace
        return len(text) if text[pos:].isspace() or pos == len(text) else None

    # Check the segment from 'pos' to 'nl_pos'
    if not text[pos:nl_pos].strip():
        return nl_pos + 1

    return None


def indent_len(text: str, pos: int = 0) -> int:
    """Counts leading whitespace of the current line starting at pos."""
    # Find end of current line
    nl_pos = text.find('\n', pos)
    end = nl_pos if nl_pos != -1 else len(text)

    # Use lstrip on the segment (slicing here is O(line_length), which is fine)
    line = text[pos:end]
    return len(line) - len(line.lstrip(' \t\f\v'))


def indent(text: str, pos: int = 0) -> int | None:
    """Matches a line break followed by leading indentation."""
    offset = empty_line(text, pos)
    if offset is None:
        return None

    amount = indent_len(text, offset)
    return amount if amount > 0 else None


def dedent(text: str, pos: int = 0) -> int | None:
    """Matches a line break that returns to the zero-margin."""
    offset = empty_line(text, pos)
    if offset is None:
        return None

    return offset if indent_len(text, offset) == 0 else None


def blank_line(text: str, pos: int = 0) -> int | None:
    """Two empty line boundaries in a row."""
    off1 = empty_line(text, pos)
    if off1 is None:
        return None

    # Note: off1 is already the absolute position for the next call
    off2 = empty_line(text, off1)
    return off2  # Returns the absolute position of the end of the second line
