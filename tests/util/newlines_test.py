# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import os

import pytest  # noqa


NL = os.linesep
LNL = len(NL)

from tatsu.util.newlines import (
    indent_len,
    take_blankline_len,
    take_dedent_len,
    take_indent_len,
    take_linebreak_len,
)


def test_empty_line():
    assert take_linebreak_len("") == 0
    assert take_linebreak_len("   ") == 3
    assert take_linebreak_len(f"{NL}") == LNL
    assert take_linebreak_len(f"  {NL}next") == 2 + LNL
    assert take_linebreak_len("content") is None


def test_indent_len():
    assert indent_len("no space") == 0
    assert indent_len("  two spaces") == 2
    assert indent_len("\t tab") == 2
    assert indent_len(f"  multi{NL}line") == 2


def test_take_indent():
    # Valid: empty line followed by actual indent
    assert take_indent_len(f"{NL}  code") == 2 + LNL
    # Invalid: empty line followed by zero margin
    assert take_indent_len(f"{NL}no indent") == LNL
    # Invalid: no initial empty line/newline
    assert take_indent_len("code") is None


def test_dedent():
    assert take_dedent_len(f"{NL}code") == LNL
    assert take_dedent_len(f"{NL}  code") is None


def test_blank_line():
    assert take_linebreak_len(f"{NL}") == LNL
    assert take_linebreak_len(f"{NL}{NL}") == LNL
    assert take_linebreak_len(f"{NL}{NL}", 1) == LNL
    assert take_blankline_len(f"{NL}{NL}") == 2 * LNL
    assert take_blankline_len(f"{NL}  {NL}") == 2 + 2 * LNL
    assert take_blankline_len(f"{NL}content") is None


def test_indent_len_with_pos():
    text = "ignore  two spaces"
    # Starting at index 6 ('  two spaces')
    assert indent_len(text, start=6) == 2


def test_indent_with_pos():
    text = f"{NL}  code"
    assert take_indent_len(text) == 2 + LNL
    text = f"ignore{NL}  code"
    assert take_indent_len(text, start=6) == 2 + LNL


def test_blank_line_with_pos():
    # text with a blank line in the middle (start 4 is the second {NL})
    text = f"abc{NL}{NL}def"
    # Starting at the first newline
    assert take_blankline_len(text, start=3) == 2 * LNL
    # Starting at the second newline
    assert take_blankline_len(text, start=4) is None


def test_blank_line_with_whitespace_and_pos():
    # text with a line containing only spaces in the middle
    text = f"abc{NL}    {NL}def"
    # start 4 is the start of the 4 spaces
    assert take_blankline_len(text, start=3) is not None


def test_not_blank_line_with_pos():
    text = f"abc{NL}  code{NL}"
    # start 4 is '  code' - should not be blank
    assert take_blankline_len(text, start=4) is None


def test_blank_line_at_end_with_pos():
    text = f"abc{NL}    "
    # start 4 is the trailing whitespace at the end of the file
    assert take_blankline_len(text, start=4) is not None
