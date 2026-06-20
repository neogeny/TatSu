# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import time
from typing import Any


__all__ = ["Bar", "Row"]


class Bar:
    def __init__(self, width: int = -1, fill: str = "█>░"):
        self.width: int = width
        self.fill: str = (fill + " " * 3)[:3]

        self._pos: int = 0
        self._top: int = 100

    def update(self, pos: int, top: int) -> None:
        self._pos = pos
        self._top = top

    def render(self, budget: int) -> str:
        fill = list(self.fill + " " * 3)[:3]
        done, head, todo = fill
        if self._top <= 0:
            return ""
        done_w = int(self._pos / self._top * budget)
        todo_w = budget - done_w
        dones = (done * done_w + head)[:-done_w]
        todos = todo * todo_w
        rendered = f"{dones}{todos}"
        # raise RuntimeError(
        #     f"{fill=!r} {budget=}\n"
        #     f"{self._pos=} {self._top=}\n"
        #     f"{done_w=} {todo_w=}\n"
        #     f"{done=!r} {head=!r} {todo=!r}\n"
        #     f"{rendered}"
        # )
        return rendered


class Row:
    """A rich, lightweight, fully picklable data object given to the user."""

    def __init__(
        self,
        label: str = "",
        cols: list[str | Bar] | None = None,
        *,
        fill: str = "█>░",
        pos: int = 0,
        top: int = 100,
    ):
        self.bar = Bar(fill=fill)
        if cols:
            self.cols = cols
        elif label:
            self.cols = [label, self.bar]
        else:
            self.cols = [self.bar]

        self.fill = fill
        self.pos: int = pos
        self.top: int = top

        self.start: float = 0.0
        self.stopped: bool = False
        self.stop_on_complete: bool = True

    def stop(self) -> None:
        self.stopped = True

    def is_stopped(self) -> bool:
        return self.stopped

    def update(self, value: int, total: int = -1):
        """Write-only operation from the user's side."""
        if total != -1:
            self.top = total
        self.pos = max(0, min(value, self.top))
        if self.stop_on_complete and self.pos >= self.top:
            self.stop()

    @dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
    class Metrics:
        pos: int
        top: int
        pct: float
        start: float
        elapsed: float
        remaining: float
        bar: Bar

    def metrics(self) -> Metrics:
        elapsed: float = time.time() - self.start

        pct: float = self.pos / self.top if self.top else 0.0
        remaining: float = elapsed / pct if pct else 0.0

        self.bar.update(self.pos, self.top)

        return self.Metrics(
            pos=self.pos,
            top=self.top,
            start=self.start,
            pct=pct,
            elapsed=elapsed,
            remaining=remaining,
            bar=self.bar,
        )

    def render(self, m: Metrics) -> list[Any]:
        fields = dataclasses.asdict(m)
        return [c.format(fields) if isinstance(c, str) else c for c in self.cols]

    def _call_render(self) -> list[Any]:
        if self.start <= 0.0:
            self.start = time.time()
        return self.render(self.metrics())
