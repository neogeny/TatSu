# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


"""Multi-bar display manager with a background rendering thread."""

import copy
import multiprocessing
import shutil
import sys
import threading
import time
from typing import Any, TextIO

from ..debugging import prints
from ..ztyle import visual_len as vlen
from .escapes import (
    blankpad,
    clearlines,
    hide_cursor,
    pushup,
    show_cursor,
)
from .row import BarRow


MAXW = shutil.get_terminal_size().columns - 1
MAXL = shutil.get_terminal_size().lines - 1


_screen_lock = multiprocessing.Lock()


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
        self.lock = threading.Lock()
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
            self.rows = [*self.rows, row]

    def insert_row(self, index: int, row: BarRow) -> None:
        """Inserts a row at the given index."""
        with self.lock:
            self.rows = [*self.rows[:index], row, *self.rows[index:]]

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
        self.out.write(hide_cursor())  # Hide cursor
        self.out.write("\n")  # Hide cursor
        self.out.flush()
        try:
            while self.alive:
                self.render_rows()
                time.sleep(1 / self.fps)
        finally:
            self.out.write(show_cursor())  # Show cursor
            self.out.flush()
        self.render_rows(final=True)

    def _take_snapshot(self) -> list[BarRow]:
        with self.lock:
            self.rows = [r for r in self.rows if r.is_active()]
            return [copy.deepcopy(r) for r in self.rows]

    def render_rows(self, *, final: bool = False) -> None:
        snapshot: list[BarRow] = self._take_snapshot()
        lines: list[list[Any]] = [b._call_render() for b in snapshot]

        colwidth = [self.line_col_widths(line, MAXW) for line in lines]
        assert len(colwidth) == len(lines)

        screenshot_lines: list[str] = [
            self.line_shot(line, cw) for line, cw in zip(lines, colwidth)
        ][-MAXL:]
        screenshot: str = clearlines(screenshot_lines)

        h = len(screenshot_lines)
        c = max(0, self.height - h)
        if c and not final:
            screenshot += blankpad(c)

        self.out.write(pushup(self.height))
        self.out.write(screenshot)
        self.out.flush()
        self.height = max(h, self.height)

    def line_shot(self, line: list[Any], cw: list[int]) -> str:
        return ''.join(f"{col:{w}}" for col, w in zip(line, cw))

    def line_col_widths(self, line: list[Any], maxw: int) -> list[int]:
        def colwidth(col: Any) -> int:
            match col:
                case str() as s:
                    return vlen(s)
                case _:
                    return len(col)

        cw = [0] * len(line)
        fill: set[int] = set()
        for j, col in enumerate(line):
            w = colwidth(col)
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

        return cw
