# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


def is_rich_library_available() -> bool:
    try:
        import rich  # noqa: F401

        return True
    except ImportError:
        return False
