# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time
from typing import Any

from ..colorize import visual_len as vlen
from ..debugging import prints
from .bar import Bar, Row


class Multi:
    def __init__(self, bars: list[Row], /, fps: int = 30):
        self._lock = threading.Lock()
        self._bars = bars
        self._running = False
        self._thread = None
        self._out = sys.stderr
        self._fps = fps

        self._height: int = 0
        self._msg_height: int = 0

    def add_bar(self, bar: Row) -> None:
        """Stores a bar internally."""
        with self._lock:
            self._bars.append(bar)

    def insert_bar(self, index: int, bar: Row) -> None:
        """Inserts a bar at the given index."""
        with self._lock:
            self._bars.insert(index, bar)

    def print(self, *args, **kwargs) -> None:
        """Prints to the output stream."""
        s = prints(*args, **kwargs)
        self.insert_bar(self._msg_height, Row(cols=[s]))
        self._msg_height += 1

    def start(self):
        """Starts the completely isolated background rendering thread."""
        self._running = True
        self._out.write("\033[?25l")  # Hide cursor
        self._out.flush()

        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Gracefully shuts down the rendering thread."""
        self._running = False
        if self._thread:
            self._thread.join()
        # Final render already ran, cursor is past bars
        self._out.write("\033[?25h")  # Show cursor
        self._out.flush()

    def _render_loop(self):
        """The isolated thread handler. Read-only side."""
        t0 = time.perf_counter()
        while self._running:
            with self._lock:
                snapshot = copy.copy(self._bars)
                self._bars = [b for b in self._bars if not b.stopped]

            self.render_bars(snapshot)
            elapsed = time.perf_counter() - t0
            dt = 1 / self._fps - elapsed
            if dt > 0:
                time.sleep(dt)
            t0 = time.perf_counter()

        with self._lock:
            snapshot = copy.copy(self._bars)
        for b in snapshot:
            b.stop()
        self.render_bars(snapshot, final=True)

    @staticmethod
    def _render_col(col: Any, w: int) -> str:
        s = ""
        match col:
            case Bar() as bar:
                rendered = bar.render(w)
                while vlen(rendered) > w:
                    rendered = rendered.replace(bar.fill[1], "")
                    if vlen(rendered) > w:
                        rendered = rendered.replace(bar.fill[0], "")
                return rendered
            case str():
                s = col
            case _:
                s = str(col)
        return f"{s!s:>{w}}"

    def render_bars(self, snapshot: list[Row], *, final: bool = False) -> int:
        if not snapshot:
            return 0
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
                        cw[j] = len(s)
                    case Bar(width=width):
                        if width <= 0:
                            fill.add(j)
                        else:
                            cw[j] = width
                    case _:
                        cw[j] = len(str(col))

            budget = max(0, maxw - sum(cw))
            while fill and budget > 0:
                w = round((0.5 + budget) / len(fill))
                budget -= w
                j = fill.pop()
                cw[j] = w

        linestr = []
        for i, line in enumerate(lines):
            parts = [self._render_col(col, colw[i][j]) for j, col in enumerate(line)]
            s = f"{''.join(parts):{maxw}}"
            linestr.append(s)

        try:
            for s in linestr:
                self._out.write(f"\033[K{s}\n")

            h = len(linestr)
            for _ in range(max(0, self._height - h)):
                self._out.write("\033[K\n")
            self._height = max(h, self._height)
        finally:
            self._out.write(f"\033[{self._height}A")
            self._out.flush()
        self._colw = colw
        return h
