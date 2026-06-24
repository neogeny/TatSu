# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""Column identifiers for bar layouts (label, counters, timings)."""

from __future__ import annotations

from enum import StrEnum, auto


__all__ = ["Col"]


class Col(StrEnum):
    # Progress Counters
    begun = auto()
    state = auto()
    pos = auto()
    total = auto()
    label = auto()

    padding = auto()
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
