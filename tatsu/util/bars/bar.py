# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import datetime as dt
import time
from collections import defaultdict
from typing import Any

from ..style import Style


__all__ = ["Bar", "Row"]

type Text = str | Style
type Fill = tuple[Text, Text, Text]


class Bar:
    __slots__ = ["fill", "pos", "top", "width"]

    def __init__(
        self,
        width: int = -1,
        fill: Fill = ("█", ">", "░"),
    ):
        self.width: int = width
        self.fill: Fill = fill

        self.pos: int = 0
        self.top: int = 100

    def update(self, pos: int, top: int) -> None:
        self.pos = pos
        self.top = top

    def render(self, budget: int) -> str:
        done, head, todo = self.fill
        if self.top <= 0:
            return ""
        done_w = int(self.pos / self.top * budget)
        todo_w = budget - done_w
        if self.pos < self.top:
            dones = str(done) * (done_w - 1) + str(head)
        else:
            dones = str(done) * done_w
        todos = str(todo) * todo_w
        rendered = f"{dones}{todos}"
        # raise RuntimeError(
        #     f"{fill=!r} {budget=}\n"
        #     f"{self._pos=} {self._top=}\n"
        #     f"{done_w=} {todo_w=}\n"
        #     f"{done=!r} {head=!r} {todo=!r}\n"
        #     f"{rendered}"
        # )
        return rendered

    def trim_to_width(self, budget: int, rendered: str) -> str:
        from ..style import visual_len as vlen

        while vlen(rendered) > budget:
            rendered = rendered.replace(str(self.fill[1]), "")
            if vlen(rendered) > budget:
                rendered = rendered.replace(str(self.fill[0]), "")
        return rendered


class Row:
    """A rich, lightweight, fully picklable data object given to the user."""

    def __init__(
        self,
        label: str = "",
        cols: list[str | Bar] | None = None,
        *,
        fill: Fill = ("█", ">", "░"),
        pos: int = 0,
        top: int = 100,
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
        label: str
        pos: int
        top: int
        pct: float
        start: float
        elapsed: float
        remaining: float
        bar: Bar
        el: dt.timedelta
        h: int
        m: int
        s: int
        ms: int

    def metrics(self) -> Metrics:
        elapsed: float = time.time() - self.start
        ms = int((elapsed % 1) * 1000)
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        el = dt.timedelta(seconds=elapsed)

        pct: float = self.pos / self.top if self.top else 0.0
        remaining: float = elapsed / pct if pct else 0.0

        self.bar.update(self.pos, self.top)

        return self.Metrics(
            label=self.label,
            pos=self.pos,
            top=self.top,
            start=self.start,
            pct=pct,
            elapsed=elapsed,
            remaining=remaining,
            bar=self.bar,
            el=el,
            h=h,
            m=m,
            s=s,
            ms=ms,
        )

    def render(self, m: Metrics) -> list[Any]:
        return self.cols

    def _call_render(self) -> list[Any]:
        if self.start <= 0.0:
            self.start = time.time()

        m = self.metrics()
        fields: dict[str, Any] = defaultdict(str)
        fields.update(dataclasses.asdict(m))
        return [c.format(**fields) if isinstance(c, str) else c for c in self.render(m)]
