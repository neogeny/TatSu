# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time
from typing import assert_never

from .bar import Bar, barType
from .line import Col, ExactWidth, FillWidthT, LeftJust, MinWidthT, RightJust


class Multi:
    def __init__(self, bars: list[Bar], /, fps: int = 30):
        self._lock = threading.Lock()
        self._bars = bars
        self._running = False
        self._thread = None
        self._out = sys.stderr
        self._fps = fps

    def add_bar(self, bar: Bar) -> None:
        """Stores a bar internally."""
        with self._lock:
            self._bars.append(bar)

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
        prev_height = 0
        t0 = time.perf_counter()
        while self._running:
            with self._lock:
                snapshot = copy.copy(self._bars)
                self._bars = [b for b in self._bars if not b.stopped]

            prev_height = self.render_bars(snapshot, prev_height=prev_height)
            elapsed = time.perf_counter() - t0
            dt = 1 / self._fps - elapsed
            if dt > 0:
                time.sleep(dt)
            t0 = time.perf_counter()

        # Final render: stop all remaining bars and show final state
        with self._lock:
            snapshot = copy.copy(self._bars)
        for b in snapshot:
            b.stop()
        self.render_bars(snapshot, prev_height=prev_height, final=True)

    @staticmethod
    def _render_col(col: Col, w: int) -> str:
        if isinstance(col.text, barType):
            return col.text.render(w)
        match col.width:
            case RightJust():
                s = f"{col.text:>{w}}"
                return s if len(s) <= w else s[-w:]
            case LeftJust():
                s = f"{col.text:<{w}}"
                return s if len(s) <= w else s[:w]
            case ExactWidth():
                s = f"{col.text:<{w}}"
                return s if len(s) <= w else s[:w]
            case MinWidthT():
                return f"{col.text:<{w}}"
            case FillWidthT():
                return f"{col.text:<{w}}"
            case _:
                assert_never()

    def render_bars(self, snapshot: list[Bar], *, prev_height: int = 0, final: bool = False) -> int:
        if not snapshot:
            return 0
        lines = [b._call_render() for b in snapshot]
        ncols = max(len(line) for line in lines)
        term = shutil.get_terminal_size().columns
        maxw = term - 1  # one shy to avoid terminal auto-wrap on \n

        # Phase 1: size each column from the first line that has it
        colw = [0] * ncols
        fill = []
        for j in range(ncols):
            col = next(line[j] for line in lines if j < len(line))
            match col.width:
                case ExactWidth(w) | LeftJust(w) | RightJust(w):
                    colw[j] = w
                case MinWidthT():
                    widths = []
                    for line in lines:
                        if j < len(line):
                            t = line[j].text
                            if isinstance(t, str):
                                widths.append(len(t))
                    colw[j] = max(widths) if widths else 0
                case FillWidthT():
                    fill.append(j)
                case _:
                    assert_never()

        # Phase 2: distribute remaining space to fill columns
        fixed = sum(colw)
        if fill:
            per = max(0, maxw - fixed) // len(fill)
            for j in fill:
                colw[j] = per

        # Phase 3: build line strings and trim to terminal width
        linestr = []
        for line in lines:
            parts = [self._render_col(col, colw[j]) for j, col in enumerate(line)]
            s = ''.join(parts)
            if len(s) > maxw:
                s = s[:maxw]
            linestr.append(s)

        # Phase 4: write all lines, clearing leftovers from previous frame
        h = len(linestr)
        for s in linestr:
            self._out.write(f"\033[K{s}\n")
        if h < prev_height:
            for _ in range(prev_height - h):
                self._out.write("\033[K\n")
        if not final:
            self._out.write(f"\033[{max(h, prev_height)}A")
        self._out.flush()
        return h
