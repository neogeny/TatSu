# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import ClassVar, TypeAliasType

from ..colorize import Style
from .line import *  # noqa: F403
from .line import (  # noqa: F401
    Col,
    FillWidth,
    FillWidthT,
    FixedWidth,
    LeftJust,
    Line,
    MinWidth,
    MinWidthT,
    Padding,
    PaddingT,
    RightJust,
)


__all__ = ["barType", "Bar"]


@dataclass(slots=True, kw_only=True)
class barType:
    pos: int
    top: int
    done: str | Style = "█"
    todo: str | Style = "░"

    def __post_init__(self):
        if self.top < self.pos:
            self.top = self.pos + 1

    def render(self, budget: int) -> str:
        if self.top == 0:
            return ""
        done_width = int(budget * self.pos / self.top)
        todo_width = int(budget * (self.top - self.pos) / self.top)
        return f"{str(self.done) * done_width}" + f"{str(self.todo) * todo_width}"


@dataclass(slots=True, kw_only=True)
class Bar:
    """A rich, lightweight, fully picklable data object given to the user."""

    done: str | Style = "█"
    todo: str | Style = "░"

    label: str | Style = ""
    top: int = 100
    pos: int = 0
    start_time: float = 0.0
    stopped: bool = False
    stop_on_complete: bool = True

    Line: ClassVar[TypeAliasType] = Line

    def stop(self) -> None:
        self.stopped = True

    def is_stopped(self) -> bool:
        return self.stopped

    def update(self, value: int, top: int = -1):
        """Write-only operation from the user's side."""
        if top != -1:
            self.top = top
        self.pos = max(0, min(value, self.top))
        if self.stop_on_complete and self.pos >= self.top:
            self.stop()

    @dataclass
    class Metrics:
        bar: Bar

        pct: float
        elapsed: float
        remaining: float

        def bart(
            self,
            pos: int = -1,
            top: int = -1,
            done: str | Style = "",
            todo: str | Style = "",
        ) -> barType:
            return barType(
                pos=pos if pos >= 0 else self.bar.pos,
                top=top if top > 0 else self.bar.top,
                done=done or self.bar.done,
                todo=todo or self.bar.todo,
            )

        @property
        def done(self) -> str | Style:
            return self.bar.done

        @property
        def todo(self) -> str | Style:
            return self.bar.todo

        @property
        def label(self) -> str | Style:
            return self.bar.label

        @property
        def top(self) -> int:
            return self.bar.top

        @property
        def pos(self) -> int:
            return self.bar.pos

        @property
        def stopped(self) -> bool:
            return self.bar.stopped

        @property
        def start_time(self) -> float:
            return self.bar.start_time

    def metrics(self) -> Metrics:
        elapsed: float = time.time() - self.start_time

        pct: float = self.pos / self.top if self.top else 0.0
        remaining: float = elapsed / pct if pct else 0.0

        return self.Metrics(
            bar=self,
            pct=pct,
            elapsed=elapsed,
            remaining=remaining,
        )

    def render(self, m: Metrics) -> Line:

        w = len(str(m.top))
        return [
            Col(MinWidth, f"{m.label} "),
            Col(RightJust(2 * (w + 1)), f"{m.pos:>{w}}/{m.top} "),
            Col(FillWidth, m.bart()),  # noqa: F821
        ]

    def _call_render(self) -> Line:
        if self.start_time <= 0.0:
            self.start_time = time.time()
        return self.render(self.metrics())
