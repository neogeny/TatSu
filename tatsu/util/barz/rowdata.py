# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import time
import uuid
from enum import IntEnum, auto

from ..ztyle import Style


__all__ = ["State", "BarRowData", "bar_time_ns"]


def bar_time_ns() -> int:
    # WARNING Time is a crucial concept when dealing with concurrency
    # WARNING and wanting to calculate elapsed time accurately.
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


class State(IntEnum):
    NEW = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


class BarRowData:
    def __new__(cls, *args, **kwargs):
        new = super().__new__(cls)
        new._uuid = uuid.uuid4().hex  # type: ignore
        return new

    @property
    def uuid(self) -> str:
        return self._uuid  # type: ignore

    def __init__(
        self,
        *,
        pos: int = 0,
        total: int = -1,
        label: str | Style = "",
        fill: str = "=>.",
        cols: list[Any] | None = None,
        style: list[Style] | None = None,
        stop_on_complete: bool = True,
    ):
        self.pos: int = 0
        self.total: int = max(1, total)
        self.label = label
        self.fill = fill
        self.style: list[Style] = style or []
        self.stop_on_complete: bool = stop_on_complete

        self.cols: list[Any] = []
        if cols is not None:
            self.cols = cols
        elif label:
            self.cols = [Col.label, Col.bar]
        else:
            self.cols = [Col.label, Col.bar]

        self.start_time: int = 0
        self.state: State = State.NEW
