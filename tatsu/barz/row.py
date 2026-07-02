# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""Progress bar row with lifecycle (NEW→RUNNING→STOPPED) and rendering."""

from __future__ import annotations

from enum import IntEnum, auto
from typing import Any

from ..packetz import WithID
from ..util import clock_time_μs  # noqa: PLC2403
from ..ztyle import Style
from .col import Col
from .metrics import Metrics


__all__ = ["BarRow", "State"]


class State(IntEnum):
    NEW = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


class BarRow(WithID):
    """A lightweight, fully picklable data object given to the user."""

    def __init__(
        self,
        *,
        pos: int = 0,
        total: int = -1,
        label: str | Style = "",
        width: int = 0,
        fill: str = "=>.",
        style: list[Style] | None = None,
        cols: list[Any] | None = None,
        selfstop: bool = True,
    ):
        self.begun: int = 0
        self.state: State = State.NEW
        self.selfstop: bool = selfstop

        self.pos: int = pos
        self.total: int = max(1, total)

        self.width: int = width
        self.fill = fill
        self.style: list[Style] = style or []

        self.label = label
        self._cols: list[Any] = []
        if cols is not None:
            self._cols = cols
        elif label:
            self._cols = [Col.label, Col.bar]
        else:
            self._cols = [Col.bar]

    @property
    def cols(self) -> list[Any]:
        return self._cols

    @property
    def key(self) -> float:
        if self.total <= 0:
            return 1
        else:
            return self.total / (1 + self.pos)

    def start(self) -> None:
        self.state = State.RUNNING
        self.begun = clock_time_μs()

    def stop(self) -> None:
        if self.state == State.NEW:
            self.state = State.STOPPING
        else:
            self.state = State.STOPPED

    def is_new(self) -> bool:
        return self.state == State.NEW

    def is_active(self) -> bool:
        return (
            self.has_started() and not self.is_stopped()
        ) or 1 < self.pos < self.total

    def has_started(self) -> bool:
        return self.state == State.RUNNING

    def is_stopped(self) -> bool:
        return self.state in {State.STOPPED, State.STOPPING} or self.pos >= self.total

    def is_stopping(self) -> bool:
        return self.state == State.STOPPING

    def snap(self) -> dict[str, Any]:
        return {
            name: value
            for name, value in vars(self).items()
            if not name.startswith("_")
        }

    def update(
        self,
        /,
        pos: int,
        total: int = -1,
        label: str | None = None,
        fill: str | None = None,
        style: list[Style] | None = None,  # noqa: ARG002
        cols: list[Any] | None = None,  # noqa: ARG002
        *_args,
        **_kwargs,
    ):
        """Write-only operation from the user's side."""
        if total > 0:
            self.total = total
        self.pos = max(0, min(pos, self.total))
        if label:
            self.label = label
        if fill is not None:
            self.fill = fill

    def render(self, m: Metrics) -> list[Any]:
        return [m.resolve(c) if isinstance(c, Col) else c for c in self._cols]

    def metrics(self) -> Metrics:
        return Metrics(self)

    def _call_render(self) -> list[Any]:
        if self.is_stopping() or (self.selfstop and self.pos >= self.total):
            self.stop()

        if self.is_stopped():
            return []

        return self.render(self.metrics())
