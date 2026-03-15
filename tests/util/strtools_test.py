# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
# from: https://www.unicode.org/charts/nameslist/n_2500.html
from __future__ import annotations

import pytest

from tatsu.util import countlines, lcnt, linecount, strtools


def test_visible_width():
    assert strtools.unicode_display_len("abc") == 3
    assert strtools.unicode_display_len("Python") == 6
    assert strtools.unicode_display_len("蛇") == 2
    assert strtools.unicode_display_len("🐍 Py") == 5


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", 1),
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


@pytest.mark.parametrize(
    "text, delta",
    [
        ("", 1),
        ("hello", 0),
        ("line1\nline2", 0),
        ("hello\n", 1),
        ("\n\n", 1),
        ("n\ro\r\nw", 0),
        ("n\ro\r\nw\n", 1),
        ("win\r\n", 1),
        ("mac\r", 1),
    ],
)
def test_linecount_delta(text, delta):
    assert linecount(text) - delta == len(text.splitlines())


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", False),
        ("hello", False),
        ("hello\n", True),
        ("\n\n", True),
        ("win\r\nline", True),
        ("mac\rline", True),
        ("n\ro\r\nw", True),
        ("line1\nline2", True),
    ],
)
def test_ismultiline(text, expected):
    assert strtools.ismultiline(text) == expected


@pytest.mark.parametrize(
    "text, expect, lcount",
    [
        ("", lcnt(1, 1, 0, 0), 1),
        ("x=1", lcnt(1, 0, 0, 1), 1),
        ("\n", lcnt(1, 1, 0, 0), 2),
        ("\r\n\r\n", lcnt(2, 2, 0, 0), 3),
        ("x=1\n", lcnt(1, 0, 0, 1), 2),
        ("# comment", lcnt(1, 0, 1, 0), 1),
        ("  # indented", lcnt(1, 0, 1, 0), 1),
        ("x=1 # inline", lcnt(1, 0, 0, 1), 1),
        (" \t \n#\ncode", lcnt(3, 1, 1, 1), 3),
        ("x=1\n#\n\n#\ny=2", lcnt(5, 1, 2, 2), 5),
    ],
)
def test_sloc_consistency(text, expect, lcount):
    actual = countlines(text)

    assert [text, lcount] == [text, linecount(text)]

    # Assert expect against actual quadruple, including text for context
    assert [text, actual] == [text, expect]
