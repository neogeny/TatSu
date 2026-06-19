# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import ClassVar, TypeAliasType

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
    Padding,
    PaddingT,
    RightJust,
    Text,
)


__all__ = ["barType", "Bar"]


@dataclass(slots=True, kw_only=True)
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

    done_str: str = "█"
    todo_str: str = "░"

    label: str
    total: int = 100
    done: int = 0
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
        self.done = max(0, min(value, self.total))
        if self.stop_on_complete and self.done >= self.total:
            self.stop()

    @dataclass
    class Metrics:
        bar: Bar

        pct: float
        elapsed: float
        remaining: float

        def bart(self) -> barType:
            return barType(
                done=self.done,
                total=self.total,
                done_str=self.done_str,
                todo_str=self.todo_str,
            )

        @property
        def done_str(self) -> str:
            return self.bar.done_str

        @property
        def todo_str(self) -> str:
            return self.bar.todo_str

        @property
        def label(self) -> str:
            return self.bar.label

        @property
        def total(self) -> int:
            return self.bar.total

        @property
        def done(self) -> int:
            return self.bar.done

        @property
        def stopped(self) -> bool:
            return self.bar.stopped

        @property
        def start_time(self) -> float:
            return self.bar.start_time

    def metrics(self) -> Metrics:
        elapsed: float = time.time() - self.start_time

        pct: float = self.done / self.total if self.total else 0.0
        remaining: float = elapsed / pct if pct else 0.0

        return self.Metrics(
            bar=self,
            pct=pct,
            elapsed=elapsed,
            remaining=remaining,
        )

    def render(self, m: Metrics) -> Line:

        w = len(str(m.total))
        return [
            Col(MinWidth, f"{m.label} "),
            Col(RightJust(2 * (w + 1)), f"{m.done:>{w}}/{m.total} "),
            Col(FillWidth, m.bart()),  # noqa: F821
        ]

    def _call_render(self) -> Line:
        if self.start_time <= 0.0:
            self.start_time = time.time()
        return self.render(self.metrics())
