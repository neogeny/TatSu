# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from enum import StrEnum, auto


"""Column identifiers for bar layouts (label, counters, timings)."""


__all__ = ["Col"]


class Col(StrEnum):
    label = auto()
    padding = auto()
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
