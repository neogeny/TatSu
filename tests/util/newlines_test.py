import pytest  # noqa

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
    assert take_linebreak_len("\n") == 1
    assert take_linebreak_len("  \nnext") == 3
    assert take_linebreak_len("content") is None


def test_indent_len():
    assert indent_len("no space") == 0
    assert indent_len("  two spaces") == 2
    assert indent_len("\t tab") == 2
    assert indent_len("  multi\nline") == 2


def test_take_indent():
    # Valid: empty line followed by actual indent
    assert take_indent_len("\n  code") == 3
    # Invalid: empty line followed by zero margin
    assert take_indent_len("\nno indent") == 1
    # Invalid: no initial empty line/newline
    assert take_indent_len("code") is None


def test_dedent():
    assert take_dedent_len("\ncode") == 1
    assert take_dedent_len("\n  code") is None


def test_blank_line():
    assert take_linebreak_len("\n") == 1
    assert take_linebreak_len("\n\n") == 1
    assert take_linebreak_len("\n\n", 1) == 1
    assert take_blankline_len("\n\n") == 2
    assert take_blankline_len("\n  \n") == 4
    assert take_blankline_len("\ncontent") is None


def test_indent_len_with_pos():
    text = "ignore  two spaces"
    # Starting at index 6 ('  two spaces')
    assert indent_len(text, start=6) == 2


def test_indent_with_pos():
    text = "\n  code"
    assert take_indent_len(text) == 3
    text = "ignore\n  code"
    assert take_indent_len(text, start=6) == 3


def test_blank_line_with_pos():
    # text with a blank line in the middle (start 4 is the second \n)
    text = "abc\n\ndef"
    # Starting at the first newline
    assert take_blankline_len(text, start=3) == 2
    # Starting at the second newline
    assert take_blankline_len(text, start=4) is None


def test_blank_line_with_whitespace_and_pos():
    # text with a line containing only spaces in the middle
    text = "abc\n    \ndef"
    # start 4 is the start of the 4 spaces
    assert take_blankline_len(text, start=3) is not None


def test_not_blank_line_with_pos():
    text = "abc\n  code\n"
    # start 4 is '  code' - should not be blank
    assert take_blankline_len(text, start=4) is None


def test_blank_line_at_end_with_pos():
    text = "abc\n    "
    # start 4 is the trailing whitespace at the end of the file
    assert take_blankline_len(text, start=4) is not None
