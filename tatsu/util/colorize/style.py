#!/usr/bin/env python3
from __future__ import annotations

from copy import copy
from typing import Self

from .colormap import COLORMAP
from .colormethods import ColorMethods


class Style(ColorMethods):
    def __init__(
        self,
        value: str = "",
        *,
        fg: int = -1,
        bg: int = -1,
        bold: bool = False,
        dim: bool = False,
        italic: bool = False,
        underline: bool = False,
        blink: bool = False,
        inverse: bool = False,
        hidden: bool = False,
        strikethrough: bool = False,
    ):
        self.value = value
        self._fg = fg
        self._bg = bg
        self._bold = bold
        self._dim = dim
        self._italic = italic
        self._underline = underline
        self._blink = blink
        self._inverse = inverse
        self._hidden = hidden
        self._strikethrough = strikethrough

    def fg(self, value: int) -> Self:
        new = copy(self)
        new._fg = max(0, min(value, 255))
        return new

    def bg(self, value: int) -> Self:
        new = copy(self)
        new._bg = max(0, min(value, 255))
        return new

    def fg_name(self, name: str) -> Self:
        new = copy(self)
        new._fg = COLORMAP.get(name, 0)
        return new

    def bg_name(self, name: str) -> Self:
        new = copy(self)
        new._bg = COLORMAP.get(name, 0)
        return new

    def bold(self) -> Self:
        new = copy(self)
        new._bold = True
        return new

    def dim(self) -> Self:
        new = copy(self)
        new._dim = True
        return new

    def italic(self) -> Self:
        new = copy(self)
        new._italic = True
        return new

    def underline(self) -> Self:
        new = copy(self)
        new._underline = True
        return new

    def blink(self) -> Self:
        new = copy(self)
        new._blink = True
        return new

    def inverse(self) -> Self:
        new = copy(self)
        new._inverse = True
        return new

    def hidden(self) -> Self:
        new = copy(self)
        new._hidden = True
        return new

    def strikethrough(self) -> Self:
        new = copy(self)
        new._strikethrough = True
        return new

    def apply(self, text: str) -> str:
        if not text:
            return ""

        codes: list[str] = []
        if self._bold:
            codes.append('1')
        if self._dim:
            codes.append('2')
        if self._italic:
            codes.append('3')
        if self._underline:
            codes.append('4')
        if self._blink:
            codes.append('5')
        if self._inverse:
            codes.append('7')
        if self._hidden:
            codes.append('8')
        if self._strikethrough:
            codes.append('9')
        if self._fg != -1:
            c = self._fg
            if c < 8:
                codes.append(str(30 + c))
            elif c < 16:
                codes.append(str(90 + c - 8))
            else:
                codes.append(f'38;5;{c}')
        if self._bg != -1:
            c = self._bg
            if c < 8:
                codes.append(str(40 + c))
            elif c < 16:
                codes.append(str(100 + c - 8))
            else:
                codes.append(f'48;5;{c}')
        if not codes:
            return self.value
        return f"\033[{';'.join(codes)}m{text}\033[0m"

    def __str__(self) -> str:
        return self.apply(self.value)

    def __repr__(self) -> str:
        return repr(str(self)).replace('\\x1b', '\\e')
