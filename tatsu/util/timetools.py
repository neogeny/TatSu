# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


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


@contextmanager
def timer():
    import time
    from dataclasses import dataclass

    @dataclass(slots=True)
    class Timing:
        start: float = 0.0
        _last_lap: float = 0.0
        _end: float = -1.0

        def __post_init__(self):
            now = time.perf_counter()
            self.start = now
            self._last_lap = now

        @property
        def delta(self):
            if self._end != -1.0:
                return self._end - self.start
            return time.perf_counter() - self.start

        def lap(self):
            if self._end != -1.0:
                return 0.0
            now = time.perf_counter()
            duration = now - self._last_lap
            self._last_lap = now
            return duration

    res = Timing()
    try:
        yield res
    finally:
        res._end = time.perf_counter()
