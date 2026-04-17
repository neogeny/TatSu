# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


# New grammar symbols
# >|    EOL
# ->|   EOL
# |>    INDENT
# <|    DEDENT


def empty_line(text: str) -> int | None:
    """Matches a whitespace-only line or the end of the input."""
    if not text:
        return 0

    # Check if there is a newline
    nl_pos = text.find('\n')

    if nl_pos == -1:
        # Case: No newline. If the whole string is whitespace,
        # it's a valid empty line ending at EOT.
        return len(text) if not text.strip() else None

    # Case: Newline found. Check if the line before it is whitespace.
    # strip() is efficient for small slices.
    if not text[:nl_pos].strip():
        return nl_pos + 1

    return None


def indent_len(text: str) -> int:
    """Counts leading whitespace of the first line without 'bleeding'."""
    # split('\n', 1) is O(line_length), not O(total_text)
    first_line = text.split('\n', 1)[0]
    return len(first_line) - len(first_line.lstrip(' \t\f\v'))


def indent(text: str) -> int | None:
    """Matches a line break followed by leading indentation."""
    offset = empty_line(text)
    if offset is None:
        return None

    # We look at the 'forehead' of the next part
    amount = indent_len(text[offset:])
    return (offset + amount) if amount > 0 else None


def dedent(text: str) -> int | None:
    """Matches a line break that returns to the zero-margin."""
    offset = empty_line(text)
    if offset is None:
        return None

    return offset if indent_len(text[offset:]) == 0 else None


def blank_line(text: str) -> int | None:
    """Two empty line boundaries in a row."""
    off1 = empty_line(text)
    if off1 is None:
        return None

    off2 = empty_line(text[off1:])
    if off2 is None:
        return None

    return off1 + off2
