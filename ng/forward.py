# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections.abc import Callable


def forward[T: Callable](fun: T) -> T:
    return fun


# noinspection PyOverloads
def f() -> int: ...  # pyright: ignore[reportRedeclaration]  # ty:ignore[empty-body]


def f() -> int:  # noqa: F811
    return 0
