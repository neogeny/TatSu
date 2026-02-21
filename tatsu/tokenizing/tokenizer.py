# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .cursor import Cursor


@runtime_checkable
class Tokenizer(Protocol):
    def __init__(self, *args, **kwargs): ...

    def new_cursor(self) -> Cursor: ...
