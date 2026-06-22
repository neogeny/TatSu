# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
col.py ──→ metrics.py
  │           │
  └─── row.py ┘
         │
  multi.py, main.py

Progress bars with terminal animation, multi-bar support, and color styling.
"""

from __future__ import annotations

from .bar import Bar
from .col import Col
from .main import main
from .metrics import BarRowProtocol, Metrics
from .multi import Multi
from .row import BarRow, State


__all__ = [
    "BarRow",
    "Bar",
    "BarRowProtocol",
    "Col",
    "main",
    "Metrics",
    "Multi",
    "State",
]
