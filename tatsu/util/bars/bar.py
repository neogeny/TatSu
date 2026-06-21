# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import datetime as dt
import time
from enum import IntEnum, StrEnum, auto
from typing import Any

from .. import findfirst
from ..ztyle import Style


__all__ = ["Bar", "BarRow", "Col"]


def bar_time_ns() -> int:
    # WARNING Time is a crucial concept when dealing with concurrency
    # WARNING and wanting to calculate elapsed time accurately.
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


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


class State(IntEnum):
    NEW = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


class Bar:
    def __init__(
        self,
        /,
        total: int = 1,
        *,
        width: int = 0,
        fill: str = "=>.",  # pyright: ignore[reportRedeclaration]
        style: list[Style] | None = None,
    ):
        self.pos: int = 0
        self.total: int = total
        self.width: int = width
        self.fill: str = (fill + "...")[:3]

        self.style: list[Style] = style or []
        s = Style()
        if not self.style:
            self.style = [s] * 3
        elif len(self.style) == 2:
            self.style = [*self.style, s]
        else:
            self.style = [self.style[0]] * 2 + [s]

    def __str__(self) -> str:
        return self.render(max(1, self.total))

    def __len__(self) -> int:
        return self.width

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

        return self.trim_to_width(budget, f"{dones}{todos}")

    def render_done(self, w: int) -> str:
        done = self.fill[0]
        sd = self.style[0]
        if self.pos >= self.total:
            return sd.apply(done * w)

        head = self.fill[1]
        sh = self.style[1]
        if sh == sd:
            return sd.apply(done * (w - 1) + head)
        return sd.apply(done * (w - 1)) + sh.apply(head)

    def render_todo(self, w: int) -> str:
        todo = self.fill[2]
        st = self.style[2]
        return st.apply(todo * w)

    def trim_to_width(self, budget: int, rendered: str) -> str:
        from ..ztyle import visual_len as vlen

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

    def __init__(
        self,
        *,
        pos: int = 0,
        total: int = -1,
        label: str | Style = "",
        fill: str = "=>.",
        cols: list[Any] | None = None,
        style: list[Style] | None = None,
        stop_on_complete: bool = True,
    ):
        self.pos: int = 0
        self.total: int = max(1, total)
        self.label = label
        self.fill = fill
        self.style = style
        self.stop_on_complete: bool = stop_on_complete

        self.cols: list[Any] = []
        if cols is not None:
            self.cols = cols
        elif label:
            self.cols = [Col.label, Col.bar]
        else:
            self.cols = [Col.label, Col.bar]

        self.start_time: int = 0
        self.state: State = State.NEW

    def start(self) -> None:
        self.state = State.RUNNING
        self.start_time = bar_time_ns()

    def stop(self) -> None:
        if self.state == State.NEW:
            self.state = State.STOPPING
        else:
            self.state = State.STOPPED

    def is_active(self) -> bool:
        return self.has_started() and not self.is_stopped()

    def has_started(self) -> bool:
        return self.state == State.RUNNING

    def is_stopped(self) -> bool:
        return self.state in {State.STOPPED, State.STOPPING} or self.pos >= self.total

    def is_stopping(self) -> bool:
        return self.state == State.STOPPING

    def update(self, pos: int, total: int = -1, /, *args, **kwargs):
        """Write-only operation from the user's side."""
        if total > 0:
            self.total = total
        self.pos = max(0, min(pos, self.total))

    def metrics(self) -> dict[Col, Any]:
        elapsed = max(0, bar_time_ns() - self.start_time)
        total_ms = elapsed // 10**6
        ms = total_ms % 1000
        seconds = (total_ms // 1000) % 60
        minutes = (seconds // 60) % 60
        hours, minutes = divmod(minutes, 60)
        duration = dt.timedelta(seconds=elapsed * 10e-9)

        pct = self.pos / self.total if self.total else 0.0
        percentage = 100 * pct
        total_est = elapsed / pct if pct else 0.0
        eta_seconds = max(0.0, total_est - elapsed) if total_est else 0.0
        eta_duration = dt.timedelta(seconds=eta_seconds)

        bar = Bar(fill=self.fill, style=self.style)
        bar.update(self.pos, self.total)

        return {
            Col.bar: bar,
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
        if self.is_stopping() or (self.stop_on_complete and self.pos >= self.total):
            self.stop()

        if self.is_stopped():
            return []

        return self.render(self.metrics())
