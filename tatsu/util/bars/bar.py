# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import datetime as dt
import time
from typing import Any

from ..style import Style


__all__ = ["Bar", "BarRow"]

type Text = str | Style
type Fill = tuple[Text, Text, Text]


class Bar:
    __slots__ = ["fill", "pos", "total", "width"]

    def __init__(
        self,
        width: int = -1,
        fill: Fill = ("█", ">", "░"),
    ):
        self.width: int = width
        self.fill: Fill = fill

        self.pos: int = 0
        self.total: int = 100

    def update(self, pos: int, total: int) -> None:
        self.pos = pos
        self.total = total

    def render(self, budget: int) -> str:
        done, head, todo = self.fill

        pos = self.pos
        pos = max(pos, 0)

        total = self.total
        if total <= 0:
            total = 1 + pos

        done_w = int(pos / total * budget)
        todo_w = budget - done_w

        if self.pos < self.total:
            dones = str(done) * (done_w - 1) + str(head)
        else:
            dones = str(done) * done_w

        todos = str(todo) * todo_w
        return f"{dones}{todos}"

    def trim_to_width(self, budget: int, rendered: str) -> str:
        from ..style import visual_len as vlen

        while (w := vlen(rendered)) > budget:
            chars = [
                str(self.fill[2]),
                str(self.fill[1]),
                str(self.fill[0]),
                ">",
                "-",
                "=",
                ".",
                "█",
                "░",
            ]
            for char in chars:
                rendered = rendered.replace(char, "", 1)
                if vlen(rendered) < w:
                    break
        return rendered


class BarRow:
    """A rich, lightweight, fully picklable data object given to the user."""

    def __init__(
        self,
        label: str = "",
        cols: list[str | Bar] | None = None,
        *,
        fill: Fill = ("█", ">", "░"),
        pos: int = 0,
        total: int = 100,
    ):
        self.label = label
        self.bar = Bar(fill=fill)
        if cols:
            self.cols = cols
        elif label:
            self.cols = [label, self.bar]
        else:
            self.cols = [self.bar]

        self.fill = fill
        self.pos: int = pos
        self.total: int = total

        self.start: float = 0.0
        self.stopped: bool = False
        self.stotal_on_complete: bool = True

    def stop(self) -> None:
        self.stopped = True

    def is_stotalped(self) -> bool:
        return self.stopped

    def update(self, value: int, total: int = -1):
        """Write-only operation from the user's side."""
        if total != -1:
            self.total = total
        self.pos = max(0, min(value, self.total))
        if self.stotal_on_complete and self.pos >= self.total:
            self.stop()

    from types import SimpleNamespace

    class Metrics(SimpleNamespace):
        pass

    def metrics(self) -> Metrics:
        elapsed = time.time() - self.start
        ms = int((elapsed % 1) * 1000)
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        duration = dt.timedelta(seconds=elapsed)

        pct = self.pos / self.total if self.total else 0.0
        percentage = 100 * pct
        total_est = elapsed / pct if pct else 0.0
        eta_seconds = max(0.0, total_est - elapsed) if total_est else 0.0
        eta_duration = dt.timedelta(seconds=eta_seconds)

        self.bar.update(self.pos, self.total)

        return self.Metrics(
            label=self.label,
            # Progress Counters
            n=self.pos,
            total=self.total,
            percentage=percentage,
            pct=pct,
            # Timings & Durations
            elapsed=elapsed,
            rt=duration,  # Run Time (as timedelta object)
            eta=eta_duration,  # Estimated Time Remaining (as timedelta object)
            eta_s=eta_seconds,  # Raw ETA seconds
            # Time components for custom string building
            h=hours,
            m=minutes,
            s=seconds,
            ms=ms,
            # Core components
            bar=self.bar,
        )

    def render(self, m: Metrics) -> list[Any]:
        return self.cols

    def _call_render(self) -> list[Any]:
        if self.start <= 0.0:
            self.start = time.time()

        m = self.metrics()
        fields: dict[str, Any] = m.__dict__
        return [c.format(**fields) if isinstance(c, str) else c for c in self.render(m)]
