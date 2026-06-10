#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import namedtuple
from copy import copy
from typing import Self

from .colormethods import ColorMethods


class RGB(namedtuple('RGB', ['r', 'g', 'b'])):
    __slots__ = ()

    def __new__(cls, r: int, g: int, b: int) -> Self:
        def to_byte(v: int) -> int:
            return max(0, min(v, 255))

        return super().__new__(cls, to_byte(r), to_byte(g), to_byte(b))


def rgb(r: int, g: int, b: int) -> RGB:
    return RGB(r, g, b)


class Style(ColorMethods):
    def __init__(
        self,
        value: str = "",
        *,
        fg: int | RGB | None = -1,
        bg: int | RGB | None = -1,
        bold: bool = False,
        dim: bool = False,
        italic: bool = False,
        underline: bool = False,
        blink: bool = False,
        inverse: bool = False,
        hidden: bool = False,
        strikethrough: bool = False,
        force_enable: bool | None = None,
    ):
        self.value = value
        self.enabled = sys.stdout.isatty() if force_enable is None else force_enable

        self._fg: int | RGB = -1
        self._bg: int | RGB = -1

        self._set_fg(fg)
        self._set_bg(bg)

        self._bold = bold
        self._dim = dim
        self._italic = italic
        self._underline = underline
        self._blink = blink
        self._inverse = inverse
        self._hidden = hidden
        self._strikethrough = strikethrough

    def _set_fg(self, value: int | RGB | None) -> None:
        if isinstance(value, RGB):
            self._fg = value
        elif value is None or value < 0:
            self._fg = -1
        else:
            self._fg = max(0, min(value, 255))

    def _set_bg(self, value: int | RGB | None) -> None:
        if isinstance(value, RGB):
            self._bg = value
        elif value is None or value < 0:
            self._bg = -1
        else:
            self._bg = max(0, min(value, 255))

    def fg(self, value: int | RGB | None) -> Self:
        new = copy(self)
        new._set_fg(value)
        return new

    def bg(self, value: int | RGB | None) -> Self:
        new = copy(self)
        new._set_bg(value)
        return new

    def fg_rgb(self, r: int, g: int, b: int) -> Self:
        new = copy(self)
        new._set_fg(rgb(r, g, b))
        return new

    def bg_rgb(self, r: int, g: int, b: int) -> Self:
        new = copy(self)
        new._set_bg(rgb(r, g, b))
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
        if not self.enabled:
            return text

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
        if isinstance(self._fg, RGB):
            codes.append(f'38;2;{self._fg.r};{self._fg.g};{self._fg.b}')
        elif self._fg != -1:
            c = self._fg
            if c < 8:
                codes.append(str(30 + c))
            elif c < 16:
                codes.append(str(90 + c - 8))
            else:
                codes.append(f'38;5;{c}')
        if isinstance(self._bg, RGB):
            codes.append(f'48;2;{self._bg.r};{self._bg.g};{self._bg.b}')
        elif self._bg != -1:
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
