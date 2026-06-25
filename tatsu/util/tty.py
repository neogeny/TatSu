# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import re


# Compiles standard 7-bit ANSI control sequences (CSI, SGR, etc.)
ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
SGR_RE = re.compile(r"\x1B\[([\d;]*)m")


def tty_escape(s: str) -> str:
    return s.replace('\x1b', '\\e').replace('\\x1b', '\\e')


def tty_unescape(s: str) -> str:
    return s.replace('\\e', '\x1b')


def descape(text: str | bytes) -> str:
    """Removes ANSI escape codes from a string."""
    if isinstance(text, bytes):
        text = str(text)
    if not isinstance(text, str):
        raise TypeError(f"expected str got {type(text)!r}")
    return ANSI_RE.sub("", text)


def visual_len(text: str | bytes) -> int:
    """Returns the true visual length of a string, omitting
    terminal escape codes."""
    return len(descape(text))


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
