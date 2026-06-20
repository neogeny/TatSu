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
    def __init__(self, bars: list[BarRow], /, fps: int = 60):
        self._lock = threading.Lock()
        self._bars = bars
        self._running = False
        self._thread = None
        self._out = sys.stderr
        self._fps = fps

        self._height: int = 0
        self._msg_count: int = 0

    def add_bar(self, bar: BarRow) -> None:
        """Stores a bar internally."""
        with self._lock:
            self._bars.append(bar)

    def insert_bar(self, index: int, bar: BarRow) -> None:
        """Inserts a bar at the given index."""
        with self._lock:
            self._bars.insert(index, bar)

    def print(self, *args, **kwargs) -> None:
        """Prints to the output stream."""
        s = prints(*args, end="", **kwargs)
        self.insert_bar(self._msg_count, MessageRow(cols=[s]))
        self._msg_count += 1
        # self._height += 1

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
            self.render_bars(self._take_snapshot())
            elapsed = time.perf_counter() - t0
            dt = 1 / self._fps - elapsed
            if dt > 0:
                time.sleep(dt)
                t0 = time.perf_counter()

        for b in self._bars[self._msg_count :]:
            b.stop()
        self.render_bars(self._take_snapshot(), final=True)

    def _take_snapshot(self) -> list[BarRow]:
        with self._lock:
            self._bars = [b for b in self._bars if not b.stopped]
            return copy.copy(self._bars)

    def render_bars(self, snapshot: list[BarRow], *, final: bool = False) -> None:
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
        barshot = ''.join(f"\033[K{s}\n" for s in linestr)
        h = len(linestr)

        clearshot = "\033[K\n" * (self._height - h)
        self._height = max(h, self._height)
        screenshot = barshot + clearshot
        self._out.write(screenshot)
        self._out.flush()
        if not final:
            self._out.write(f"\033[{self._height}A")
        self._height = max(h, self._height)

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
