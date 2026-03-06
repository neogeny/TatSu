# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations


type ffset = set[tuple[str, ...]]


def ref(name: str) -> tuple[str]:
    return (_ref(name),)


def kdot(x: ffset, y: ffset, k: int) -> ffset:
    if not y:
        return {a[:k] for a in x}
    elif not x:
        return {b[:k] for b in y}
    else:
        return {(a + b)[:k] for a in x for b in y}


class _ref(str):
    def __repr__(self) -> str:
        return repr(f'<{self}>')
