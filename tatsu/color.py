# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals


class _BF(object):
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


class _Style(object):
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

        global Fore, Back, Style
        Fore = colorama.Fore
        Back = colorama.Back
        Style = colorama.Style
    except ImportError:
        pass
