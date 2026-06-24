# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


_PYGMENTS_AVAILABLE: bool | None = None


def is_pygments_available() -> bool:
    global _PYGMENTS_AVAILABLE  # noqa: PLW0603
    if _PYGMENTS_AVAILABLE is None:
        try:
            import pygments  # noqa: F401
        except ImportError:
            _PYGMENTS_AVAILABLE = False
        else:
            _PYGMENTS_AVAILABLE = True
    return _PYGMENTS_AVAILABLE
