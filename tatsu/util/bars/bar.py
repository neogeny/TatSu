# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TypeAliasType

from .line import *  # noqa: F403
from .line import (  # noqa: F401
    Col,
    ExactWidth,
    FillWidth,
    FillWidthT,
    LeftJust,
    Line,
    MinWidth,
    MinWidthT,
    RightJust,
)


__all__ = ["barType", "Bar"]


@dataclass(slots=True)
class barType:
    done: int
    total: int
    done_str: str = "█"
    todo_str: str = "░"

    def __post_init__(self):
        if self.total < self.done:
            self.total = self.done + 1

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
        if self.stop_on_complete and self.current >= self.total:
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

        MinWidth: MinWidthT = MinWidth
        FillWidth: FillWidthT = FillWidth
        ExactWidth: type[ExactWidth] = ExactWidth
        Col: type[Col] = Col
        LeftJust: type[LeftJust] = LeftJust
        Line: TypeAliasType = Line  # type: ignore
        MinWidthT: type[MinWidthT] = MinWidthT
        RightJust: type[RightJust] = RightJust

        def bar(self) -> barType:
            return barType(self.current, self.total)

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

        w = len(str(m.total))
        return [
            m.Col(m.MinWidth, f"{m.label} "),
            m.Col(m.RightJust(2 * (w + 1)), f"{m.current:>{w}}/{m.total} "),
            m.Col(m.FillWidth, m.bar()),  # noqa: F821
        ]

    def _call_render(self) -> Line:
        if self.start_time <= 0.0:
            self.start_time = time.time()
        return self.render(self.metrics())
