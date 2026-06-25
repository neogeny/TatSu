from __future__ import annotations

from unittest.mock import patch

import pytest

from tatsu.ztyle.markup import parse, tokenize, tokenize_to_values
from tatsu.ztyle.style import Color, Style


@pytest.fixture(autouse=True)
def _tty_stdout():
    with patch("sys.stdout.isatty", return_value=True):
        yield


def test_plain_text():
    assert parse("hello") == "hello"


def test_plain_text_with_spaces():
    assert parse("hello world") == "hello world"


def test_single_bold():
    assert parse("[bold]hello[/bold]") == "\033[1mhello\033[0m"


def test_single_italic():
    assert parse("[italic]hello[/italic]") == "\033[3mhello\033[0m"


def test_single_color():
    assert parse("[red]hello[/red]") == "\033[31mhello\033[0m"


def test_multiple_attributes_one_tag():
    r = parse("[bold red]hello[/]")
    assert r == "\033[1;31mhello\033[0m"


def test_mixed_plain_and_styled():
    r = parse("plain [bold]bold[/bold] plain")
    assert r == "plain \033[1mbold\033[0m plain"


def test_styled_then_plain():
    r = parse("[bold]bold[/bold] plain")
    assert r == "\033[1mbold\033[0m plain"


def test_plain_then_styled():
    r = parse("plain [bold]bold[/]")
    assert r == "plain \033[1mbold\033[0m"


def test_nested_styles():
    r = parse("[bold]bold [red]red[/red] only bold[/bold]")
    assert r == "\033[1mbold \x1b[0m\x1b[1;31mred\x1b[0m\x1b[1m only bold\x1b[0m"


def test_close_all():
    r = parse("[bold red]hello[/all]world")
    assert r == "\033[1;31mhello\033[0mworld"


def test_escape_brackets():
    r = parse("[[hello]]")
    assert r == "[hello]]"


def test_empty_string():
    assert parse("") == ""


def test_color_methods():
    s = Style("hello", color=Color.always()).pink()
    r = parse("[pink]hello[/]")
    assert r == str(s)


def test_consecutive_styles():
    r = parse("[bold]a[/][italic]b[/]")
    assert r == "\033[1ma\033[0m\033[3mb\033[0m"


def test_tokenize_plain():
    toks = tokenize("hello")
    assert toks[0].value == "hello"


def test_tokenize_tag():
    toks = tokenize_to_values("[bold]hello[/]")
    assert toks == ["bold", "hello", ""]


def test_tokenize_escaped():
    toks = tokenize_to_values("[[hello]]")
    assert toks == ["[", "hello]]"]


def test_tokenize_multiple_attrs():
    toks = tokenize("[bold red]x[/]")
    assert toks[0].value == "bold red"
