# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause


def forward[T](subject: T) -> T:
    return subject


@forward
def f() -> int: ...  # pyright: ignore[reportRedeclaration]  # ty:ignore[empty-body]


assert f() is None


def f() -> int:
    return 0


assert f() == 0
