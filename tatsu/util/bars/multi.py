# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import copy
import shutil
import sys
import threading
import time
from dataclasses import dataclass
from typing import assert_never

from ..colorize.style import visual_len as vlen
from .bar import Bar, barType
from .line import (  # noqa: F401
    Col,
    FillWidthT,
    FixedWidth,
    LeftJust,
    MinWidthT,
    PaddingT,
    RightJust,
    Width,
)


@dataclass(slots=True, kw_only=True)
class MessageBar(Bar):
    def render(self, m: Bar.Metrics) -> list[Col]:
        return [Col(LeftJust(0), m.label)]


class Multi:
    def __init__(self, bars: list[Bar], /, fps: int = 30):
        self._lock = threading.Lock()
        self._bars = bars
        self._running = False
        self._thread = None
        self._out = sys.stderr
        self._fps = fps

        self._height: int = 0
        self._message_count: int = 0

    def add_bar(self, bar: Bar) -> None:
        """Appends a bar internally."""
        with self._lock:
            self._bars.append(bar)

    def insert_bar(self, at: int, bar: Bar) -> None:
        """Stores a bar at the given position."""
        with self._lock:
            self._bars.insert(at, bar)

    def print(self, *args, **kwargs):
        """Queue a message line shown above bars on the next render."""
        import io

        buf = io.StringIO()
        kwargs.pop('file', None)
        kwargs.pop('end', None)
        kwargs.pop('flush', None)
        print(*args, file=buf, **kwargs)
        line = buf.getvalue().rstrip('\n')
        # self.insert_bar(self._message_count, MessageBar(label=line))
        self._message_count += 1
        self._height += 1

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
                    return s if vlen(s) <= w else s[-w:]
                case FixedWidth() | LeftJust() | MinWidthT() | FillWidthT():
                    return f"{s!s:<{w}}"
                case _ as unreachable:
                    assert_never(unreachable)

        match col.text:
            case barType() as bt:
                rendered = bt.render(w)
                while vlen(rendered) > w:
                    rendered = rendered.replace(str(bt.todo), '', 1)
                    if vlen(rendered) > w:
                        rendered = rendered.replace(str(bt.done), '', 1)
                return rendered
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
        linecount = len(snapshot)
        lines = [b._call_render() for b in snapshot]
        maxw = shutil.get_terminal_size().columns

        colw: list[list[int]] = [[0] * len(line) for line in lines]

        for i, line in enumerate(lines):
            cw = colw[i]

            fill: set[int] = set()
            for j, col in enumerate(line):
                match col.width:
                    case FillWidthT():
                        fill.add(j)
                    case FixedWidth() as ew:  # includes LeftJust, RightJust
                        cw[j] = ew.width
                    case MinWidthT():
                        match col.text:
                            case str(s):
                                cw[j] = vlen(s)
                            case _:
                                cw[j] = vlen(str(col.text))
                    case _:
                        assert_never()

            budget = max(0, maxw - sum(cw))
            if not fill or not budget:
                continue
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

            h = linecount
            for _ in range(max(0, self._height - h)):
                self._out.write("\033[K\n")
            self._height = max(h, self._height)
        finally:
            self._out.write(f"\033[{self._height}A")
            self._out.flush()
        self._colw = colw
        return h
