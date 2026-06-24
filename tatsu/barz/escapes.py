# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def hide_cursor() -> str:
    """Returns an escape sequence that hides the cursor."""
    return "\033[?25l"


def show_cursor() -> str:
    """Returns an escape sequence that shows the cursor."""
    return "\033[?25h"


def clearline(text: str = "") -> str:
    """Returns the text prefixed with a clear-to-end-of-line escape sequence."""
    return f"\033[K{text}\n"


def shoot_lines(texts: list[str]) -> list[str]:
    """Returns a block of clear-to-end-of-line escape sequences for each line."""
    return [clearline(t) for t in texts]


def pushup(lines: int) -> str:
    """Returns an escape sequence that moves the cursor up a given number of lines."""
    return f"\033[{lines}A"


def blankpad(count: int) -> list[str]:
    """Generates a block of empty, cleared lines to wipe out stale terminal trailing rows."""
    return ["\033[K\n"] * count
