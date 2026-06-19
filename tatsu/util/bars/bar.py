# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from dataclasses import dataclass

from .line import *  # noqa: F403


DEFAULT_BAR_WIDTH = 50


@dataclass(slots=True, frozen=True)
class bar:
    done: int
    total: int
    done_str: str = "█"
    todo_str: str = "░"

    def render(self, budget: int) -> str:
        if self.total == 0:
            return ""
        done_width = int(self.done / self.total * budget)
        todo_width = budget - done_width
        return f"{self.done_str * done_width}{self.todo_str * todo_width}"


@dataclass(slots=True, kw_only=True)
class Bar:
    """A rich, lightweight, fully picklable data object given to the user."""

    label: str
    total: int = 100
    current: int = 0
    start_time: float = 0.0
    stopped: bool = False
    stop_on_complete: bool = True

    def stop(self) -> None:
        self.stopped = True

    def is_stopped(self) -> bool:
        return self.stopped

    def update(self, value: int, total: int = -1):
        """Write-only operation from the user's side."""
        if total != -1:
            self.total = total
        self.current = max(0, min(value, self.total))
        if self.stop_on_complete and self.current == self.total:
            self.stop()

    @dataclass
    class Metrics:
        label: str
        total: int
        current: int
        start_time: float

        pct: float
        elapsed: float
        remaining: float

        def bar(self) -> bar:
            return bar(self.current, self.total)

    def metrics(self) -> Metrics:
        elapsed: float = time.time() - self.start_time

        pct: float = self.current / self.total if self.total else 0.0
        remaining: float = elapsed / pct if pct else 0.0

        return self.Metrics(
            label=self.label,
            total=self.total,
            current=self.current,
            start_time=self.start_time,
            pct=pct,
            elapsed=elapsed,
            remaining=remaining,
        )

    def render(self, m: Metrics) -> Line:
        from .line import Col, FillWidth, RightJust

        w = len(str(m.total))
        return [
            Col(RightJust(2 * (w + 1)), f"{m.current:>{w}}/{m.total} "),
            Col(FillWidth, m.bar()),  # noqa: F821
        ]

    def _call_render(self) -> Line:
        if self.start_time <= 0.0:
            self.start_time = time.time()
        return self.render(self.metrics())
