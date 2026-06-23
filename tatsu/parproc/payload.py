# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class Payload(Protocol):
    path: Path
    payload: Any

    def raises(self) -> tuple[type[Exception], ...]:
        return ()


class StrPayload(str, Payload):
    __slots__ = ()

    @property
    def path(self) -> Path:  # type: ignore
        return Path(self)

    @property
    def payload(self) -> Any:  # type: ignore
        return Path(self).read_text()


@dataclass(slots=True)
class VisualPayload(Payload):
    path: Path
    payload: Any
