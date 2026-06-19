# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NamedTuple


@dataclass(slots=True, frozen=True)
class MinWidthT:
    pass


MinWidth = MinWidthT()


@dataclass(slots=True, frozen=True)
class FillWidthT:
    pass


FillWidth = FillWidthT()


@dataclass(slots=True, frozen=True)
class FixedWidth:
    width: int


@dataclass(slots=True, frozen=True)
class LeftJust(FixedWidth):
    pass


@dataclass(slots=True, frozen=True)
class RightJust(FixedWidth):
    pass


type Width = MinWidthT | FillWidthT | FixedWidth


@dataclass(slots=True, frozen=True)
class PaddingT:
    pass


Padding = PaddingT()


class Col(NamedTuple):
    width: Width
    text: Any

    def budget_width(self, budget: int) -> int:
        match self.width:
            case MinWidthT():
                return 0
            case FillWidthT():
                return budget
            case FixedWidth(w):
                return w


type Line = list[Col]
