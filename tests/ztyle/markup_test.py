from __future__ import annotations

from unittest.mock import patch

import pytest

from tatsu.ztyle.markup import markup, tokenize, tokenize_to_values


@pytest.fixture(autouse=True)  # noqa
def _tty_stdout():
    with patch("sys.stdout.isatty", return_value=True):
        yield


def test_plain_text():
    r = markup("hello")
    assert len(r.style) == 1
    assert r.style[0].value == "hello"


def test_plain_text_with_spaces():
    r = markup("hello world")
    assert len(r.style) == 1
    assert r.style[0].value == "hello world"


def test_single_bold():
    r = markup("[bold]hello[/bold]")
    assert len(r.style) == 1
    assert r.style[0].value == "hello"
    assert r.style[0]._bold is True


def test_single_italic():
    r = markup("[italic]hello[/italic]")
    assert len(r.style) == 1
    assert r.style[0].value == "hello"
    assert r.style[0]._italic is True


def test_single_color():
    r = markup("[red]hello[/red]")
    assert len(r.style) == 1
    assert r.style[0].value == "hello"
    assert r.style[0]._fg == 1


def test_multiple_attributes_one_tag():
    r = markup("[bold red]hello[/]")
    assert len(r.style) == 1
    assert r.style[0].value == "hello"
    assert r.style[0]._bold is True
    assert r.style[0]._fg == 1


def test_mixed_plain_and_styled():
    r = markup("plain [bold]bold[/bold] plain")
    assert len(r.style) == 3
    assert r.style[0].value == "plain "
    assert r.style[1].value == "bold"
    assert r.style[1]._bold is True
    assert r.style[2].value == " plain"


def test_styled_then_plain():
    r = markup("[bold]bold[/bold] plain")
    assert len(r.style) == 2
    assert r.style[0].value == "bold"
    assert r.style[0]._bold is True
    assert r.style[1].value == " plain"


def test_plain_then_styled():
    r = markup("plain [bold]bold[/]")
    assert len(r.style) == 2
    assert r.style[0].value == "plain "
    assert r.style[1].value == "bold"
    assert r.style[1]._bold is True


def test_nested_styles():
    r = markup("[bold]bold [red]red[/red] only bold[/bold]")
    assert len(r.style) == 3
    assert r.style[0].value == "bold "
    assert r.style[0]._bold is True
    assert r.style[0]._fg == -1
    assert r.style[1].value == "red"
    assert r.style[1]._bold is True
    assert r.style[1]._fg == 1
    assert r.style[2].value == " only bold"
    assert r.style[2]._bold is True
    assert r.style[2]._fg == -1


def test_close_all():
    r = markup("[bold red]hello[/all]world")
    assert len(r.style) == 2
    assert r.style[0].value == "hello"
    assert r.style[0]._bold is True
    assert r.style[0]._fg == 1
    assert r.style[1].value == "world"
    assert r.style[1]._bold is False
    assert r.style[1]._fg == -1


def test_escape_brackets():
    r = markup("[[hello]]")
    assert len(r.style) == 1
    assert r.style[0].value == "[hello]]"


def test_empty_string():
    r = markup("")
    assert len(r.style) == 0
    assert r.style == []


def test_color_methods():
    r = markup("[pink]hello[/]")
    assert len(r.style) == 1
    assert r.style[0].value == "hello"
    assert r.style[0]._fg == 200  # pink is ANSI 256-color 200


def test_consecutive_styles():
    r = markup("[bold]a[/][italic]b[/]")
    assert len(r.style) == 2
    assert r.style[0].value == "a"
    assert r.style[0]._bold is True
    assert r.style[0]._italic is False
    assert r.style[1].value == "b"
    assert r.style[1]._bold is False
    assert r.style[1]._italic is True


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
