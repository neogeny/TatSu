# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""Multi-bar display manager with a background rendering thread."""

from __future__ import annotations

import contextlib
import copy
import itertools
import multiprocessing
import shutil
import sys
import threading
import time
from typing import Any, TextIO

from ..util.debugging import prints
from ..util.primality import primes_upto
from ..util.tty import (
    blankpad,
    hide_cursor,
    pushup,
    shoot_lines,
    show_cursor,
)
from ..ztyle import visual_len as vlen
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
        fps: int = 12,  # noqa: B006
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
        self._frame: list[str] = []

    @property
    @contextlib.contextmanager
    def frame_lock(self):
        with self.lock:
            yield
        self.render_frame()

    def find_row(self, row: BarRow) -> BarRow | None:
        for r in self.rows:
            if r.id == row.id:
                return r
        return None

    def remove_row(self, id: str) -> None:
        with self.frame_lock:
            self.rows = [row for row in self.rows if row.id != id]

    def add_row(self, row: BarRow) -> None:
        """Stores a row internally."""
        if existing := self.find_row(row):
            existing.update(**row.snap())
            return
        with self.frame_lock:
            self.rows = [*self.rows, row]

    def insert_row(self, index: int, row: BarRow) -> None:
        """Inserts a row at the given index."""
        if existing := self.find_row(row):
            existing.update(**row.snap())
            return
        with self.frame_lock:
            self.rows = [*self.rows[:index], row, *self.rows[index:]]

    def insert_message(self, msg: str) -> None:
        """Inserts a message row at the bottom."""
        row = MessageRow(cols=[msg])
        with self.frame_lock:
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
        with self.frame_lock:
            row.update(**snap)

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
        last = time.monotonic()
        try:
            while self.alive:
                self.paint_frame()
                time.sleep(1 / next(fpscycle))

                now = time.monotonic()
                elapsed = now - last
                if elapsed > 1:
                    self.render_frame()
                last = now
        finally:
            self.out.write(show_cursor())  # Show cursor
            self.out.flush()
        self.render_frame(final=True)
        self.paint_frame(final=True)

    def _take_snapshot(self) -> list[BarRow]:
        with self.lock:
            snapshot = [copy.copy(r) for r in self.rows if not r.is_stopped()]
            self.rows = [r for r in self.rows if not r.is_stopped()][-MAXL:]
            self.msg_count = sum(
                1
                for _ in itertools.takewhile(
                    lambda r: isinstance(r, MessageRow), self.rows
                )
            )
            return snapshot

    def render_frame(self, *, final: bool = False):
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

        frame = [*shot_lines, *blank_lines][-MAXL:]

        self._frame = frame

    def paint_frame(self, *, final: bool = False) -> None:
        frame = self._frame
        screenshot: str = "".join(frame)
        self.out.write(screenshot)

        self.height = max(len(frame), self.height)
        with _screen_lock:
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
