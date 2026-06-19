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
from .line import (
    Col,
    ExactWidth,
    FillWidthT,
    LeftJust,
    MinWidthT,
    PaddingT,
    RightJust,
    Width,
)


class Multi:
    def __init__(self, bars: list[Bar], /, fps: int = 30):
        self._lock = threading.Lock()
        self._bars = bars
        self._running = False
        self._thread = None
        self._out = sys.stderr
        self._fps = fps

        self._colw: list[int] = []
        self._height: int = 0

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

        # Final render: stop all remaining bars and show final state
        with self._lock:
            snapshot = copy.copy(self._bars)
        for b in snapshot:
            b.stop()
        self.render_bars(snapshot, final=True)

    @staticmethod
    def _render_col(col: Col, w: int) -> str:
        def render_str(s: str) -> str:
            match col.width:
                case RightJust():
                    s = f"{s!s:>{w}}"
                    return s if len(s) <= w else s[-w:]
                case ExactWidth() | LeftJust() | MinWidthT() | FillWidthT():
                    return f"{s!s:<{w}}"
                case _ as unreachable:
                    assert_never(unreachable)

        match col.text:
            case barType() as bt:
                return bt.render(w)
            case PaddingT():
                return ' ' * w
            case str() as s:
                return render_str(s)
            case _:
                return render_str(str(col.text))

    def render_bars(self, snapshot: list[Bar], *, final: bool = False) -> int:
        #
        # ── Column width algebra ──────────────────────────────────
        #
        # Each column position j collects width specifications from
        # every bar's Line.  The renderer must reconcile them into a
        # single budget colw[j] for that column.  The reconciliation
        # is a partial order over Width types:
        #
        #   ExactWidth (incl. LeftJust, RightJust)   highest priority
        #   MinWidthT                                 middle priority
        #   FillWidthT                                lowest priority
        #
        # Rules:
        #   1. If ANY bar declares ExactWidth at column j, that
        #      column's width is fixed: colw[j] = max of all exact
        #      widths declared.  Lower-priority declarations are
        #      ignored.
        #   2. Otherwise, if ANY bar declares MinWidthT at column j,
        #      the column is content-derived: colw[j] = max string
        #      length of str-typed text across all bars.
        #   3. If all bars at column j declare FillWidthT (or make
        #      no declaration — the initial state is FillWidthT),
        #      the column gets a share of the remaining terminal
        #      width after all fixed columns are accounted for.
        #
        # coltype[j] tracks the renderer's settled decision for
        # column j, starting from the bottom (FillWidthT) so that
        # the first higher-priority declaration upgrades it.
        # fill is the set of column indices that will split the
        # remaining horizontal budget.
        #
        # ───────────────────────────────────────────────────────────
        if not snapshot:
            return 0
        lines = [b._call_render() for b in snapshot]
        ncols = max(len(line) for line in lines)
        maxw = shutil.get_terminal_size().columns

        prev_ncols = len(self._colw)
        max_ncols = max(ncols, prev_ncols)
        ncol_diff = max(0, max_ncols - prev_ncols)
        colw = self._colw + [0] * ncol_diff
        assert len(colw) == max_ncols

        coltype: list[Width] = [FillWidthT()] * max_ncols
        fill: set[int] = set()

        for line in lines:
            for j, col in enumerate(line):
                match col.width:
                    case ExactWidth() as ew:  # includes LeftJust, RightJust
                        coltype[j] = ew
                        fill.discard(j)
                        colw[j] = max(colw[j], ew.width)

                    case MinWidthT():
                        match coltype[j]:
                            case ExactWidth():
                                continue
                            case FillWidthT():
                                coltype[j] = col.width
                        match col.text:
                            case str(s):
                                colw[j] = max(colw[j], len(s))

                    case FillWidthT():
                        match coltype[j]:
                            case FillWidthT():
                                coltype[j] = col.width
                                fill.add(j)
                            case _:
                                continue

                    case _:
                        raise AssertionError('unreachable')

        if fill:
            budget = max(0, maxw - sum(colw))
            if budget:
                per = budget // len(fill)
                for j in fill:
                    colw[j] = per

        linestr = []
        for line in lines:
            parts = [self._render_col(col, colw[j]) for j, col in enumerate(line)]
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
