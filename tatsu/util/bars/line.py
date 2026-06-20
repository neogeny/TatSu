# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:
    from .bar import Bar


@dataclass(slots=True, frozen=True)
class MinWidthT:
    pass


MinWidth = MinWidthT()


@dataclass(slots=True, frozen=True)
class FillWidthT:
    pass


FillWidth = FillWidthT()


@dataclass(slots=True, frozen=True)
class ExactWidth:
    width: int


@dataclass(slots=True, frozen=True)
class LeftJust(ExactWidth):
    pass


@dataclass(slots=True, frozen=True)
class RightJust(ExactWidth):
    pass


type Width = MinWidthT | FillWidthT | ExactWidth


@dataclass(slots=True, frozen=True)
class PaddingT:
    pass


Padding = PaddingT()

type Text = str | Bar | PaddingT


class Col(NamedTuple):
    width: Width
    text: Text

    def budget_width(self, budget: int) -> int:
        match self.width:
            case MinWidthT():
                return 0
            case FillWidthT():
                return budget
            case ExactWidth(w):
                return w


type Line = list[Col]
