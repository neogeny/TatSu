# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from enum import IntEnum, auto
from typing import Any

from ..ztyle import Style
from .metrics import Col, Metrics


__all__ = ["BarRow", "Col"]


def bar_time_ns() -> int:
    # WARNING Time is a crucial concept when dealing with concurrency
    # WARNING and wanting to calculate elapsed time accurately.
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


class State(IntEnum):
    NEW = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


class BarRow:
    """A lightweight, fully picklable data object given to the user."""

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

    def is_new(self) -> bool:
        return self.state == State.NEW

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

    def render(self, m: Metrics) -> list[Any]:
        return [getattr(m, c.value) if isinstance(c, Col) else c for c in self.cols]

    def _call_render(self) -> list[Any]:
        if self.is_stopping() or (self.stop_on_complete and self.pos >= self.total):
            self.stop()

        if self.is_stopped():
            return []

        return self.render(Metrics(self))
