# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Protocol


class Heart(Protocol):
    def beat(self, mark: int, total: int) -> None: ...


class NullHeart:
    def beat(self, mark: int, total: int) -> None:
        pass
