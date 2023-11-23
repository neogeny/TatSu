# ruff: noqa: PLW0603
from __future__ import annotations


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


def init():
    try:
        import colorama

        colorama.init()
    except ImportError:
        return

    global Fore, Back, Style  # pylint: disable=global-statement
    Fore = colorama.Fore
    Back = colorama.Back
    Style = colorama.Style
