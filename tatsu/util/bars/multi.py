# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time
from typing import assert_never

from .bar import Bar, bar
from .line import ExactWidth, FillWidthT, LeftJust, MinWidthT, RightJust


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
        # Clean up terminal lines
        with self._lock:
            num_bars = len(self._bars)
        self._out.write(f"\033[{num_bars}B\n\033[?25h")
        self._out.flush()

        if self._thread:
            self._thread.join()

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

    def render_bars(self, snapshot: list[Bar]) -> None:
        if not snapshot:
            return
        lines = [b._call_render() for b in snapshot]
        ncols = max(len(line) for line in lines)
        term = shutil.get_terminal_size().columns

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
            per = max(0, term - fixed) // len(fill)
            for j in fill:
                colw[j] = per

        # Phase 3: build line strings and trim to terminal width
        linestr = []
        for line in lines:
            parts = []
            for j, col in enumerate(line):
                w = colw[j]
                parts.append(
                    col.text.render(w)
                    if isinstance(col.text, bar)
                    else f"{col.text:>{w}}"
                )
            s = ''.join(parts)
            # Trim to terminal width to prevent wrap/overflow
            if len(s) > term:
                s = s[:term]
            linestr.append(s)

        # Phase 4: write all lines (after trimming they won't wrap)
        for s in linestr:
            self._out.write(f"\033[K{s}\n")
        self._out.write(f"\033[{len(linestr)}A")
        self._out.flush()
