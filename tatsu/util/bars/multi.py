# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time
from typing import TextIO

from ..debugging import prints
from ..ztyle import visual_len as vlen
from .bar import BarRow


class MessageRow(BarRow):
    def is_active(self) -> bool:
        # NOTE Lie to always get rendered
        return True

    def has_started(self) -> bool:
        return True

    def is_stopping(self) -> bool:
        return False

    def is_stopped(self) -> bool:
        return False


class Multi:
    def __init__(
        self,
        rows: list[BarRow],
        /,
        fps: int = 60,
        out: TextIO = sys.stderr,
    ):
        self.lock = threading.RLock()
        self.rows = rows
        self.alive = False
        self.worker = None
        self.out = out
        self.fps = fps

        self.height: int = 0
        self.msg_count: int = 0

    def add_row(self, row: BarRow) -> None:
        """Stores a row internally."""
        with self.lock:
            self.rows.append(row)

    def insert_row(self, index: int, row: BarRow) -> None:
        """Inserts a row at the given index."""
        with self.lock:
            self.rows.insert(index, row)

    def insert_message(self, msg: str) -> None:
        """Inserts a message row at the bottom."""
        row = MessageRow(cols=[msg])
        self.insert_row(self.msg_count, row)
        self.msg_count += 1

    def print(self, *args, **kwargs) -> None:
        """Prints to the output stream."""
        kwargs.pop("file", None)
        kwargs.pop("highlight", None)
        kwargs.pop("markup", None)
        s = prints(*args, end="", **kwargs)
        if not s:
            self.insert_message("")
        for msg in s.splitlines():
            self.insert_message(msg)

    def start(self):
        """Starts the completely isolated background rendering thread."""
        self.alive = True

        self.worker = threading.Thread(target=self._render_loop, daemon=True)
        self.worker.start()

    def stop(self):
        """Gracefully shuts down the rendering thread."""
        with self.lock:
            for row in self.rows:
                row.stop()
                row.stop()

        self.alive = False
        if self.worker:
            self.worker.join()

    def _render_loop(self):
        """The isolated thread handler. Read-only side."""
        self.out.write(_hide_cursor())  # Hide cursor
        self.out.write("\n")  # Hide cursor
        self.out.flush()
        try:
            while self.alive:
                self.render_rows()
                time.sleep(1 / self.fps)
        finally:
            self.out.write(_show_cursor())  # Show cursor
            self.out.flush()
        self.render_rows(final=True)

    def _take_snapshot(self) -> list[BarRow]:
        with self.lock:
            self.rows = [r for r in self.rows if r.is_active()]
            return [copy.deepcopy(r) for r in self.rows]

    def render_rows(self, *, final: bool = False) -> None:
        snapshot: list[BarRow] = self._take_snapshot()
        if not snapshot:
            return
        lines = [b._call_render() for b in snapshot]
        maxw = shutil.get_terminal_size().columns - 1

        colwidth: list[list[int]] = [[0] * len(line) for line in lines]
        assert len(colwidth) == len(lines)

        for i, line in enumerate(lines):
            fill: set[int] = set()
            cw = colwidth[i]
            for j, col in enumerate(line):
                match col:
                    case str() as s:
                        cw[j] = vlen(s)
                    case _:
                        w = len(col)
                        if w <= 0:
                            fill.add(j)
                        else:
                            cw[j] = w

            budget = max(0, maxw - sum(cw))
            while fill and budget > 0:
                count = len(fill)
                w = round(((1 / count) + budget) / count)
                budget -= w
                j = fill.pop()
                cw[j] = w

        screenshot_lines: list[str] = [
            ''.join(f"{col:{w}}" for col, w in zip(line, cw))
            for line, cw in zip(lines, colwidth)
        ]

        h = len(screenshot_lines)
        c = self.height - h
        screenshot: str = _clearlines(screenshot_lines)
        if not final:
            screenshot += _blankpad(c)

        self.out.write(_pushup(self.height))
        self.out.write(screenshot)
        self.out.flush()
        self.height = max(h, self.height)


def _hide_cursor() -> str:
    """Returns an escape sequence that hides the cursor."""
    return "\033[?25l"


def _show_cursor() -> str:
    """Returns an escape sequence that shows the cursor."""
    return "\033[?25h"


def _clearline(text: str = "") -> str:
    """Returns the text prefixed with a clear-to-end-of-line escape sequence."""
    return f"\033[K{text}\n"


def _clearlines(texts: list[str]) -> str:
    """Returns a block of clear-to-end-of-line escape sequences for each line."""
    return "".join(_clearline(t) for t in texts)


def _pushup(lines: int) -> str:
    """Returns an escape sequence that moves the cursor up a given number of lines."""
    return f"\033[{lines}A"


def _blankpad(count: int) -> str:
    """Generates a block of empty, cleared lines to wipe out stale terminal trailing rows."""
    return "\033[K\n" * count
