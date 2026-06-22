# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

"""Computed metrics and column resolution for a progress bar row."""

import datetime as dt
from functools import cached_property
from typing import Any, Protocol

from .. import clock_time_ns
from ..ztyle import Style
from .bar import Bar
from .col import Col


__all__ = ["BarRowProtocol", "Metrics"]


class BarRowProtocol(Protocol):
    label: str | Style
    pos: int
    total: int
    fill: str
    style: list[Style]
    width: int
    start_time: int


class Metrics:
    """Lazy, cached metrics for a BarRow. Create fresh per render cycle."""

    def __init__(self, row: BarRowProtocol) -> None:
        self.row = row

    def resolve(self, col: Col) -> Any:
        return getattr(self, col.value)

    @property
    def label(self) -> str | Style:
        return self.row.label

    @property
    def padding(self) -> str:
        return " "

    @property
    def pos(self) -> int:
        return self.row.pos

    @property
    def total(self) -> int:
        return self.row.total

    @property
    def fill(self) -> str:
        return self.row.fill

    @property
    def style(self) -> list[Style]:
        return self.row.style or []

    @property
    def width(self) -> int:
        return self.row.width

    @property
    def start_time(self) -> int:
        return self.row.start_time

    # -- computed, cached lazily --
    @cached_property
    def elapsed(self) -> int:
        return max(0, clock_time_ns() - self.start_time)

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
        b = Bar(
            fill=self.fill,
            style=self.style,
            width=self.width,
        )
        b.update(self.pos, self.total)
        return b
