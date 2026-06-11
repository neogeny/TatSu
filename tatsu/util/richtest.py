# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import types


def is_rich_library_available() -> bool:
    try:
        import rich  # noqa: F401  # pyright: ignore[reportMissingImports]

        return True
    except ImportError:
        return False


def get_rich() -> types.ModuleType:
    import rich  # noqa: F401  # pyright: ignore[reportMissingImports]

    return rich
