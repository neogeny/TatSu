import pytest  # noqa

from tatsu.util.newlines import (
    blank_line,
    dedent,
    empty_line,
    indent,
    indent_len,
)


def test_empty_line():
    assert empty_line("") == 0
    assert empty_line("   ") == 3
    assert empty_line("\n") == 1
    assert empty_line("  \nnext") == 3
    assert empty_line("content") is None


def test_indent_len():
    assert indent_len("no space") == 0
    assert indent_len("  two spaces") == 2
    assert indent_len("\t tab") == 2
    assert indent_len("  multi\nline") == 2


def test_indent():
    # Valid: empty line followed by actual indent
    assert indent("\n  code") == 2
    # Invalid: empty line followed by zero margin
    assert indent("\nno indent") is None
    # Invalid: no initial empty line/newline
    assert indent("code") is None


def test_dedent():
    # Valid: empty line followed by zero margin
    assert dedent("\ncode") == 1
    # Invalid: empty line followed by an indent
    assert dedent("\n  code") is None


def test_blank_line():
    # Two empty lines (\n followed by \n)
    assert blank_line("\n\n") == 2
    # One empty line followed by a whitespace line
    assert blank_line("\n  \n") == 4
    assert blank_line("\ncontent") is None


def test_indent_len_with_pos():
    text = "ignore  two spaces"
    # Starting at index 6 ('  two spaces')
    assert indent_len(text, pos=6) == 2


def test_indent_with_pos():
    text = "ignore\n  code"
    # Starting at index 6 ('\n  code')
    assert indent(text, pos=6) == 2


def test_blank_line_with_pos():
    # text with a blank line in the middle (pos 4 is the second \n)
    text = "abc\n\ndef"
    # Starting at the first newline
    assert blank_line(text, pos=3)
    # Starting at the second newline
    assert blank_line(text, pos=4) is None


def test_blank_line_with_whitespace_and_pos():
    # text with a line containing only spaces in the middle
    text = "abc\n    \ndef"
    # pos 4 is the start of the 4 spaces
    assert blank_line(text, pos=3)


def test_not_blank_line_with_pos():
    text = "abc\n  code\n"
    # pos 4 is '  code' - should not be blank
    assert blank_line(text, pos=4) is None


def test_blank_line_at_end_with_pos():
    text = "abc\n    "
    # pos 4 is the trailing whitespace at the end of the file
    assert blank_line(text, pos=4) is not None
