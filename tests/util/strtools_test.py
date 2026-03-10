# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# from: https://www.unicode.org/charts/nameslist/n_2500.html
from __future__ import annotations

import pytest

from tatsu.util import linecount, strtools


def test_visible_width():
    assert strtools.unicode_display_len("abc") == 3
    assert strtools.unicode_display_len("Python") == 6
    assert strtools.unicode_display_len("蛇") == 2
    assert strtools.unicode_display_len("🐍 Py") == 5


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", 0),
        ("hello", 1),
        ("hello\n", 2),
        ("\n\n", 3),
        ("win\r\nline", 2),
        ("mac\rline", 2),
        ("n\ro\r\nw", 3),
        ("line1\nline2", 2),
    ],
)
def test_visual_linecount(text, expected):
    assert linecount(text) == expected


@pytest.mark.parametrize("text, delta", [
    ("", 0),
    ("hello", 0),
    ("line1\nline2", 0),
    ("hello\n", 1),
    ("\n\n", 1),
    ("n\ro\r\nw", 0),
    ("n\ro\r\nw\n", 1),
    ("win\r\n", 1),
    ("mac\r", 1),
])
def test_linecount_delta(text, delta):
    assert linecount(text) - delta == len(text.splitlines())
