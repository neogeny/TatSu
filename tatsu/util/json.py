# Copyright (c) 2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Any


type JSONValue = (
    dict[str, JSONValue] | list[JSONValue] | str | int | float | bool | None
)


def ensure_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f'Expected dict, got {type(value).__name__}')
    return value
