# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

# ruff: noqa: PLW0603


class Color:
    BLACK = ''
    BLUE = ''
    CYAN = ''
    GREEN = ''
    MAGENTA = ''
    RED = ''
    RESET = ''
    WHITE = ''
    YELLOW = ''
    LIGHTBLACK_EX = ''
    LIGHTRED_EX = ''
    LIGHTGREEN_EX = ''
    LIGHTYELLOW_EX = ''
    LIGHTBLUE_EX = ''
    LIGHTMAGENTA_EX = ''
    LIGHTCYAN_EX = ''
    LIGHTWHITE_EX = ''

    BLACK_BG = ''
    BLUE_BG = ''
    CYAN_BG = ''
    GREEN_BG = ''
    MAGENTA_BG = ''
    RED_BG = ''
    RESET_BG = ''
    WHITE_BG = ''
    YELLOW_BG = ''
    LIGHTBLACK_EX_BG = ''
    LIGHTRED_EX_BG = ''
    LIGHTGREEN_EX_BG = ''
    LIGHTYELLOW_EX_BG = ''
    LIGHTBLUE_EX_BG = ''
    LIGHTMAGENTA_EX_BG = ''
    LIGHTCYAN_EX_BG = ''
    LIGHTWHITE_EX_BG = ''

    BRIGHT = ''
    DIM = ''
    NORMAL = ''
    RESET_ALL = ''


def init():
    try:
        import colorama

        colorama.init()
    except ImportError:
        return

    global Fore, Back, Style
    Fore = colorama.Fore
    Back = colorama.Back
    Style = colorama.Style

    colors = {}
    colors.update({name: value for name, value in vars(Fore).items() if name.isupper()})
    colors.update(
        {name + '_BG': value for name, value in vars(Back).items() if name.isupper()}
    )
    colors.update(
        {name: value for name, value in vars(Style).items() if name.isupper()}
    )

    for name, value in colors.items():
        setattr(Color, name, value)


class _BF:
    BLACK = ''
    BLUE = ''
    CYAN = ''
    GREEN = ''
    MAGENTA = ''
    RED = ''
    RESET = ''
    WHITE = ''
    YELLOW = ''
    LIGHTBLACK_EX = ''
    LIGHTRED_EX = ''
    LIGHTGREEN_EX = ''
    LIGHTYELLOW_EX = ''
    LIGHTBLUE_EX = ''
    LIGHTMAGENTA_EX = ''
    LIGHTCYAN_EX = ''
    LIGHTWHITE_EX = ''


class _Fore(_BF):
    pass


class _Back(_BF):
    pass


class _Style:
    BRIGHT = ''
    DIM = ''
    NORMAL = ''
    RESET_ALL = ''


Fore = _Fore
Back = _Back
Style = _Style
