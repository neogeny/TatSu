# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import datetime as dt
import time
from enum import StrEnum, auto
from functools import cached_property
from typing import TYPE_CHECKING, Any

from .bar import Bar


if TYPE_CHECKING:
    from .row import BarRow


__all__ = ["Col", "Metrics", "bar_time_ns"]


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


class Metrics:
    """Lazy, cached metrics for a BarRow. Create fresh per render cycle."""

    def __init__(self, row: BarRow) -> None:
        self.row = row

    def resolve(self, col: Col) -> Any:
        return getattr(self, col.value)

    # -- trivial passthrough (not cached, no computation) --

    @property
    def label(self):
        return self.row.label

    @property
    def pos(self):
        return self.row.pos

    @property
    def total(self):
        return self.row.total

    # -- computed, cached lazily --

    @cached_property
    def elapsed(self) -> int:
        if self.row.is_new():
            return 0
        return max(0, bar_time_ns() - self.row.start_time)

    @cached_property
    def rt(self) -> dt.timedelta:
        return dt.timedelta(seconds=self.elapsed / 1_000_000_000)

    @cached_property
    def pct(self) -> float:
        return self.pos / self.total if self.total else 0.0

    @cached_property
    def percentage(self) -> float:
        return 100 * self.pct

    @cached_property
    def eta_s(self) -> float:
        if not self.pct:
            return 0.0
        return max(0.0, self.elapsed / self.pct - self.elapsed)

    @cached_property
    def eta(self) -> dt.timedelta:
        return dt.timedelta(seconds=self.eta_s)

    @cached_property
    def h(self) -> int:
        return self.elapsed // 3_600_000_000_000

    @cached_property
    def m(self) -> int:
        return (self.elapsed // 60_000_000_000) % 60

    @cached_property
    def s(self) -> int:
        return (self.elapsed // 1_000_000_000) % 60

    @cached_property
    def ms(self) -> int:
        return (self.elapsed // 1_000_000) % 1000

    @cached_property
    def bar(self):
        b = Bar(fill=self.row.fill, style=self.row.style)
        b.update(self.row.pos, self.row.total)
        return b
