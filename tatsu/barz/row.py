# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""Progress bar row with lifecycle (NEW→RUNNING→STOPPED) and rendering."""

from __future__ import annotations

from enum import IntEnum, auto
from typing import Any

from ..parproc.packetz import WithID
from ..util import clock_time_μs  # noqa: PLC2403
from ..ztyle import Style
from .col import Col
from .metrics import Metrics


__all__ = ["BarRow", "State"]


class State(IntEnum):
    NEW = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


class BarRow(WithID):
    """A lightweight, fully picklable data object given to the user."""

    def __init__(
        self,
        *,
        pos: int = 0,
        total: int = -1,
        label: str | Style = "",
        width: int = 0,
        fill: str = "=>.",
        style: list[Style] | None = None,
        cols: list[Any] | None = None,
        stop_on_complete: bool = True,
    ):
        self.start_time: int = 0
        self.state: State = State.NEW
        self.label = label

        self.pos: int = 0
        self.total: int = max(1, total)
        self.cols: list[Any] = []

        self.width: int = width
        self.fill = fill
        self.style: list[Style] = style or []
        self.stop_on_complete: bool = stop_on_complete

        if cols is not None:
            self.cols = cols
        elif label:
            self.cols = [Col.label, Col.bar]
        else:
            self.cols = [Col.bar]

    def start(self) -> None:
        self.state = State.RUNNING
        self.start_time = clock_time_μs()

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

    def update(
        self,
        pos: int,
        total: int = -1,
        /,
        label: str = "",
        *args,
        **kwargs,
    ):
        """Write-only operation from the user's side."""
        if total > 0:
            self.total = total
        self.pos = max(0, min(pos, self.total))
        if label:
            self.label = label

    def render(self, m: Metrics) -> list[Any]:
        return [m.resolve(c) if isinstance(c, Col) else c for c in self.cols]

    def metrics(self) -> Metrics:
        return Metrics(self)

    def _call_render(self) -> list[Any]:
        if self.is_stopping() or (self.stop_on_complete and self.pos >= self.total):
            self.stop()

        if self.is_stopped():
            return []

        return self.render(self.metrics())
