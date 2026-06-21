# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import datetime as dt
import time
from enum import StrEnum, auto
from typing import Any

from .. import findfirst
from ..style import Style


__all__ = ["Bar", "BarRow", "Col"]


class Col(StrEnum):
    label = auto()
    # Progress Counters
    pos = auto()
    total = auto()
    percentage = auto()
    pct = auto()
    # Timings & Durations
    elapsed = auto()
    rt = auto()  # Run Time (as timedelta object)
    eta = auto()  # Estimated Time Remaining (as timedelta object)
    eta_s = auto()  # Raw ETA seconds
    # Time components for custom string building
    h = auto()
    m = auto()
    s = auto()
    ms = auto()
    # Core components
    bar = auto()


class State(StrEnum):
    new = auto()
    stopping = auto()
    stopped = auto()


class Bar:
    def __init__(
        self,
        /,
        total: int = 1,
        *,
        width: int = -1,
        fill: str = "=>.",  # pyright: ignore[reportRedeclaration]
        style: list[Style] | None = None,
    ):
        self.pos: int = 0
        self.total: int = total
        self.width: int = width
        self.fill: str = (fill + "...")[:3]
        self.style: list[Style] = style or []

        s = Style()
        self.style += [s] * (3 - len(self.style))

    def __str__(self) -> str:
        return self.render(max(1, self.total))

    def __format__(self, fmt: str) -> str:
        ws = findfirst(r"(\d+).?", fmt)
        w = int(ws) if ws else self.total
        return self.render(w)

    def update(self, pos: int, total: int, fill: str | None = None) -> None:
        self.pos = pos
        self.total = total
        if fill is not None:
            self.fill = fill

    def render(self, budget: int) -> str:
        total = max(1, self.pos, self.total)

        pos = self.pos
        pos = max(0, min(total, self.pos))

        done_w = int(pos / total * budget)
        todo_w = budget - done_w

        dones = self.render_done(done_w)
        todos = self.render_todo(todo_w)

        return f"{dones}{todos}"

    def render_done(self, w: int) -> str:
        done = self.fill[0]
        head = self.fill[1]
        sd = self.style[0]
        if self.pos < self.total:
            sh = self.style[1]
            return sd.apply(done * (w - 1)) + sh.apply(head)
        return sd.apply(done * w)

    def render_todo(self, w: int) -> str:
        todo = self.fill[2]
        st = self.style[2]
        return st.apply(todo * w)

    def trim_to_width(self, budget: int, rendered: str) -> str:
        from ..style import visual_len as vlen

        while (w := vlen(rendered)) > budget:
            chars = [
                self.fill[1],
                self.fill[2],
                self.fill[0],
                "█",
                "░",
                ">",
                "-",
                "=",
                ".",
            ]
            for char in chars:
                rendered = rendered.replace(char, "", 1)
                if vlen(rendered) < w:
                    break
        return rendered


# TODO Should rename to Progress for consistency with other progress bars
class BarRow:
    """A rich, lightweight, fully picklable data object given to the user."""

    Col: type[Col] = Col

    def __init__(
        self,
        *,
        pos: int = 0,
        total: int = 100,
        label: str | Style = "",
        fill: str = "=>.",
        cols: list[str | Col] | None = None,
        style: list[Style] | None = None,
        stop_on_complete: bool = True,
    ):
        self.pos: int = 0
        self.total: int = max(1, total)
        self.label = label
        self.fill = fill
        self.style = style
        self.stop_on_complete: bool = stop_on_complete

        self.cols: list[str | Col] = []
        if cols is not None:
            self.cols = cols
        elif label:
            self.cols = [Col.label, Col.bar]
        else:
            self.cols = [Col.label, Col.bar]

        self.start: float = 0.0
        self.state: State = State.new

    def stop(self) -> None:
        if self.state == State.new:
            self.state = State.stopping
        else:
            self.state = State.stopped

    def is_stopped(self) -> bool:
        return self.state == State.stopped

    def is_stopping(self) -> bool:
        return self.state in {State.stopping, State.stopped}

    def update(self, pos: int, total: int = -1, /, *args, **kwargs):
        """Write-only operation from the user's side."""
        if total > 0:
            self.total = total
        self.pos = max(0, min(pos, self.total))
        if self.stop_on_complete and self.pos >= self.total:
            self.stop()

    from types import SimpleNamespace

    def metrics(self) -> dict[Col, Any]:
        if not self.start:
            self.start = time.time()
        elapsed = time.time() - self.start
        ms = int((elapsed % 1) * 1000)
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        duration = dt.timedelta(seconds=elapsed)

        pct = self.pos / self.total if self.total else 0.0
        percentage = 100 * pct
        total_est = elapsed / pct if pct else 0.0
        eta_seconds = max(0.0, total_est - elapsed) if total_est else 0.0
        eta_duration = dt.timedelta(seconds=eta_seconds)

        bar = Bar(fill=self.fill, style=self.style)
        bar.update(self.pos, self.total)

        return {
            Col.label: self.label,
            # Progress Counters
            Col.pos: self.pos,
            Col.total: self.total,
            Col.percentage: percentage,
            Col.pct: pct,
            # Timings & Durations
            Col.elapsed: elapsed,
            Col.rt: duration,  # Run Time (as timedelta object)
            Col.eta: eta_duration,  # Estimated Time Remaining (as timedelta object)
            Col.eta_s: eta_seconds,  # Raw ETA seconds
            Col.bar: bar,
            # Time components for custom string building
            Col.h: hours,
            Col.m: minutes,
            Col.s: seconds,
            Col.ms: ms,
        }

    def render(self, metrics: dict[Col, Any]) -> list[Any]:
        cols = self.cols
        return [metrics[c] if isinstance(c, Col) else c for c in cols]

    def _call_render(self) -> list[Any]:
        if self.is_stopping():
            return []

        if self.start <= 0.0:
            self.start = time.time()

        return self.render(self.metrics())
