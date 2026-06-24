# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import itertools


"""Multi-bar display manager with a background rendering thread."""

import copy
import multiprocessing
import shutil
import sys
import threading
import time
from typing import Any, TextIO

from ..util.debugging import prints
from ..util.primality import primes_upto
from ..ztyle import visual_len as vlen
from .escapes import (
    blankpad,
    hide_cursor,
    pushup,
    shoot_lines,
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
        fps: int = 60,  # noqa: B006
        out: TextIO = sys.stderr,
    ):
        self.lock = threading.RLock()
        self.rows = rows[:]
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
        with self.lock:
            self.insert_row(self.msg_count, row)
            self.msg_count += 1

    def update_row(self, snap: dict[str, Any]) -> None:
        """Inserts or updates a row internally."""
        if not (row_id := snap.get("id")):
            return

        for row in self.rows:
            if row.id == row_id:
                break
        else:
            row = BarRow()
            row.id = row_id
            self.add_row(row)

        row.update(**snap)

        row.start()

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
        fpscycle = itertools.cycle(primes_upto(self.fps, 11))
        try:
            while self.alive:
                self.render_rows()
                time.sleep(1 / next(fpscycle))
        finally:
            self.out.write(show_cursor())  # Show cursor
            self.out.flush()
        self.render_rows(final=True)

    def _take_snapshot(self) -> list[BarRow]:
        with self.lock:
            return [copy.copy(r) for r in self.rows if r.is_active()]

    def render_rows(self, *, final: bool = False) -> None:
        snapshot: list[BarRow] = self._take_snapshot()
        rendered: list[list[Any]] = [b._call_render() for b in snapshot]

        colwidth = [self.line_col_widths(line, MAXW) for line in rendered]
        assert len(colwidth) == len(rendered)

        expanded: list[str] = [
            self.expand_row(line, cw) for line, cw in zip(rendered, colwidth)
        ]

        shot_lines = shoot_lines(expanded)

        h = len(expanded)
        c = max(0, self.height - h) if not final else 0
        blank_lines = blankpad(c)

        frame_lines = [*shot_lines, *blank_lines]

        screenshot: str = "".join(frame_lines)
        with _screen_lock:
            self.out.write(screenshot)

        self.height = max(h, self.height)
        if not final:
            self.out.write(pushup(self.height))
        self.out.flush()

    def expand_row(self, line: list[Any], cw: list[int]) -> str:
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
