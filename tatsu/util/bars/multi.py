# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time

from .bar import Bar, bar


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
        colcount = max(len(line) for line in lines)
        colwidth: list[int] = [0] * colcount
        for line in lines:
            for j, w in enumerate(line):
                if colwidth[j] < 0:
                    continue

                if isinstance(w, str):
                    colwidth[j] = max(colwidth[j], len(w))
                    continue

                assert isinstance(w, bar)
                colwidth[j] = min(colwidth[j], w.wanted_width)

        totalwidth = sum(w for w in colwidth if w >= 0)
        budget = max(0, shutil.get_terminal_size().columns - totalwidth)
        tobudget = sum(1 for w in colwidth if w <= 0)
        percol = budget // tobudget if tobudget else 0
        for i, w in enumerate(colwidth):
            if w >= 0:
                continue
            colwidth[i] = percol

        linestr = [
            "".join(
                col.render(colwidth[i])
                if isinstance(col, bar)
                else f"{col!s:>{colwidth[i]}}"
                for i, col in enumerate(line)
            )
            for line in lines
        ]
        for s in linestr:
            self._out.write(f"{s}\n\033[K")

        self._out.write(f"\033[{len(snapshot)}A")
        self._out.flush()
