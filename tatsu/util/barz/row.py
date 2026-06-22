# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any

from .col import Col
from .metrics import Metrics
from .rowdata import BarRowData, State, bar_time_ns


__all__ = ["BarRow"]


class BarRow(BarRowData):
    """A lightweight, fully picklable data object given to the user."""

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
        return [m.resolve(c) if isinstance(c, Col) else c for c in self.cols]

    def metrics(self) -> Metrics:
        return Metrics(self)

    def _call_render(self) -> list[Any]:
        if self.is_stopping() or (self.stop_on_complete and self.pos >= self.total):
            self.stop()

        if self.is_stopped():
            return []

        return self.render(self.metrics())
