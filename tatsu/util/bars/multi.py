# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time
from typing import Any

from ..debugging import prints
from ..style import Style, visual_len as vlen
from .bar import Bar, BarRow


class MessageRow(BarRow):
    pass


class Multi:
    def __init__(self, rows: list[BarRow], /, fps: int = 60):
        self.lock = threading.Lock()
        self.rows = rows
        self.alive = False
        self.worker = None
        self.out = sys.stderr
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

    def insert_message(self, row: MessageRow) -> None:
        """Inserts a message row at the bottom."""
        self.insert_row(self.msg_count, row)
        self.msg_count += 1
        self.height += 1

    def print(self, *args, **kwargs) -> None:
        """Prints to the output stream."""
        s = prints(*args, end="", **kwargs)
        self.insert_message(MessageRow(cols=[s]))

    def start(self):
        """Starts the completely isolated background rendering thread."""
        self.alive = True

        self.worker = threading.Thread(target=self._render_loop, daemon=True)
        self.worker.start()

    def stop(self):
        """Gracefully shuts down the rendering thread."""
        self.out.write(_show_cursor())  # Show cursor
        self.out.flush()

        self.rows = self._take_snapshot()
        with self.lock:
            for row in self.rows:
                match row:
                    case MessageRow():
                        continue
                    case _:
                        row.stop()

        self.alive = False
        if self.worker:
            self.worker.join()

    def _render_loop(self):
        """The isolated thread handler. Read-only side."""
        t0 = time.perf_counter()
        with self.lock:
            self.height = len(self.rows)
        self.out.write(_hide_cursor())  # Hide cursor
        self.out.flush()
        try:
            while self.alive:
                self.render_rows(self._take_snapshot())
                elapsed = time.perf_counter() - t0
                dt = 1 / self.fps - elapsed
                if dt > 0:
                    time.sleep(dt)
                    t0 = time.perf_counter()
        finally:
            self.out.write(_show_cursor())  # Show cursor
            self.out.flush()
        self.render_rows(self._take_snapshot(), final=True)

    def _take_snapshot(self) -> list[BarRow]:
        with self.lock:
            self.rows = [r for r in self.rows if not r.stopped]
            return [copy.copy(r) for r in self.rows]

    def render_rows(self, snapshot: list[BarRow], *, final: bool = False) -> None:
        if not snapshot:
            return
        lines = [b._call_render() for b in snapshot]
        maxw = shutil.get_terminal_size().columns

        colw: list[list[int]] = [[0] * len(line) for line in lines]
        assert len(colw) == len(lines)

        for i, line in enumerate(lines):
            fill: set[int] = set()
            cw = colw[i]
            for j, col in enumerate(line):
                match col:
                    case str() as s:
                        cw[j] = vlen(s)
                    case Bar(width=width):
                        if width <= 0:
                            fill.add(j)
                        else:
                            cw[j] = width
                    case Style() as sty:
                        cw[j] = len(sty)
                    case _:
                        cw[j] = vlen(str(col))

            budget = max(0, maxw - sum(cw) - 1)
            while fill and budget > 0:
                count = len(fill)
                w = round(((1 / count) + budget) / count)
                budget -= w
                j = fill.pop()
                cw[j] = w

        linestr = [
            ''.join(self._render_col(col, colw[i][j]) for j, col in enumerate(line))
            for i, line in enumerate(lines)
        ]

        h = len(linestr)
        screenshot = _clearlines(linestr)
        if not final:
            screenshot += _blankpad(self.height - h)

        self.out.write(screenshot)
        self.out.flush()

        if not final:
            self.out.write(_pushup(self.height))

        self.height = max(h, self.height)

    @staticmethod
    def _render_col(col: Any, w: int) -> str:
        s = ""
        match col:
            case Bar() as bar:
                rendered = bar.render(w)
                rendered = bar.trim_to_width(w, rendered)
                return rendered
            case str():
                s = col
            case _:
                s = str(col)
        return f"{s!s:>{w}}"


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
