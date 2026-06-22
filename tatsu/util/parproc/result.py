# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from typing import Any


@dataclass(slots=True, order=True)
class Result:
    stop: Event
    payload: Any
    outcome: Any = None
    exception: Any = None
    linecount: int = 0
    runtime: float = 0
    memory: int = 0

    @property
    def success(self):
        return self.exception is None

    def __str__(self):
        return str(self.__dict__)
