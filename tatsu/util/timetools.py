# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import dataclasses
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


__all__ = [
    'iso_logpath',
    'iso_timestamp',
    'timer',
    'Timing',
]


def iso_timestamp() -> str:
    """
    Returns an ISO 8601 string with UTC timezone (Z).
    Example: '2026-02-15T22-15-01Z'
    """
    now = datetime.now(UTC)
    isostr = now.isoformat(timespec='seconds')
    return isostr.replace(':', '-').replace('+00-00', 'Z')


def iso_logpath(prefix: str, basdir: str = "log", suffix='.log') -> Path:
    """Helper to generate a pathlib.Path using the ISO timestamp."""
    ts = iso_timestamp()
    logdir = Path(basdir)
    logdir.mkdir(parents=True, exist_ok=True)
    suffix = suffix if suffix.startswith('.') else '.' + suffix
    return logdir / f"{prefix}_{ts}{suffix}"


@dataclasses.dataclass(slots=True)
class Timing:
    start: int = 0
    _last_lap: int = 0
    _end: int = -1

    def __post_init__(self):
        now = time.monotonic_ns()
        self.start = now
        self._last_lap = now

    @property
    def delta(self) -> float:
        if self._end >= 0:
            ns_delta = self._end - self.start
        else:
            ns_delta = time.monotonic_ns() - self.start
        return ns_delta / 1_000_000_000

    def lap(self) -> float:
        if self._end >= 0:
            return 0.0
        now = time.monotonic_ns()
        ns_duration = now - self._last_lap
        self._last_lap = now
        return ns_duration / 1_000_000_000

    def __str__(self) -> str:
        d = self.delta
        return (
            f"{int(d // 60)}m {d % 60:.2f}s"
            if d >= 60
            else f"{d:.3f}s"
            if d >= 1
            else f"{d * 1000:.2f}ms"
        )


@contextmanager
def timer() -> Generator[Timing, None, None]:
    res = Timing()
    try:
        yield res
    finally:
        res._end = time.monotonic_ns()
