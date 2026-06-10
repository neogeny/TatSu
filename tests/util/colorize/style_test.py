from __future__ import annotations

from unittest.mock import patch

import pytest

from tatsu.util.colorize.style import RGB, Style, Color, rgb


@pytest.fixture(autouse=True)
def _tty_stdout():
    with patch("sys.stdout.isatty", return_value=True):
        yield


def test_default_empty():
    assert not str(Style())


def test_value_only():
    assert str(Style('hello')) == 'hello'


def test_fg_standard():
    for idx, sgr in enumerate(range(30, 38)):
        assert str(Style('x', fg=idx)) == f'\033[{sgr}mx\033[0m'


def test_fg_bright():
    for idx, sgr in enumerate(range(90, 98)):
        assert str(Style('x', fg=idx + 8)) == f'\033[{sgr}mx\033[0m'


def test_fg_256():
    assert str(Style('x', fg=16)) == '\033[38;5;16mx\033[0m'
    assert str(Style('x', fg=255)) == '\033[38;5;255mx\033[0m'


def test_bg_standard():
    for idx, sgr in enumerate(range(40, 48)):
        assert str(Style('x', bg=idx)) == f'\033[{sgr}mx\033[0m'


def test_bg_bright():
    for idx, sgr in enumerate(range(100, 108)):
        assert str(Style('x', bg=idx + 8)) == f'\033[{sgr}mx\033[0m'


def test_bg_256():
    assert str(Style('x', bg=16)) == '\033[48;5;16mx\033[0m'
    assert str(Style('x', bg=255)) == '\033[48;5;255mx\033[0m'


def test_value_with_fg():
    assert str(Style('hello', fg=1)) == '\033[31mhello\033[0m'


def test_modifier_bold():
    assert str(Style('x').bold()) == '\033[1mx\033[0m'


def test_modifier_dim():
    assert str(Style('x').dim()) == '\033[2mx\033[0m'


def test_modifier_italic():
    assert str(Style('x').italic()) == '\033[3mx\033[0m'


def test_modifier_underline():
    assert str(Style('x').underline()) == '\033[4mx\033[0m'


def test_modifier_blink():
    assert str(Style('x').blink()) == '\033[5mx\033[0m'


def test_modifier_inverse():
    assert str(Style('x').inverse()) == '\033[7mx\033[0m'


def test_modifier_hidden():
    assert str(Style('x').hidden()) == '\033[8mx\033[0m'


def test_modifier_strikethrough():
    assert str(Style('x').strikethrough()) == '\033[9mx\033[0m'


def test_modifier_combination():
    s = Style('x').bold().italic().underline()
    assert str(s) == '\033[1;3;4mx\033[0m'


def test_fg_with_modifier():
    s = Style('x').bold().fg(1)
    assert str(s) == '\033[1;31mx\033[0m'


def test_full_composition():
    s = Style('text', fg=2, bg=7, bold=True, italic=True)
    assert str(s) == '\033[1;3;32;47mtext\033[0m'



def test_named_color_method():
    s = Style('x').pink()
    assert str(s) == '\033[38;5;200mx\033[0m'


def test_named_color_bg_method():
    s = Style('x').pink_bg()
    assert str(s) == '\033[48;5;200mx\033[0m'


def test_chained_named_color():
    s = Style('x').bold().pink()
    assert str(s) == '\033[1;38;5;200mx\033[0m'


def test_repr_escapes():
    s = Style('hi', fg=1)
    r = repr(s)
    assert '\\e[31m' in r
    assert '\\e[0m' in r


def test_rgb_constructor():
    assert str(Style('x', fg=rgb(255, 0, 0))) == '\033[38;2;255;0;0mx\033[0m'


def test_rgb_constructor_bg():
    assert str(Style('x', bg=rgb(0, 255, 0))) == '\033[48;2;0;255;0mx\033[0m'


def test_rgb_both():
    s = Style('x', fg=rgb(255, 0, 0), bg=rgb(0, 0, 255))
    assert str(s) == '\033[38;2;255;0;0;48;2;0;0;255mx\033[0m'


def test_fg_rgb_method():
    s = Style('x').fg_rgb(128, 128, 128)
    assert str(s) == '\033[38;2;128;128;128mx\033[0m'


def test_bg_rgb_method():
    s = Style('x').bg_rgb(64, 64, 64)
    assert str(s) == '\033[48;2;64;64;64mx\033[0m'


def test_rgb_chained_with_modifier():
    s = Style('x').bold().fg_rgb(255, 0, 255)
    assert str(s) == '\033[1;38;2;255;0;255mx\033[0m'


def test_rgb_clamp():
    assert str(Style('x', fg=rgb(-10, 300, 128))) == '\033[38;2;0;255;128mx\033[0m'


def test_rgb_from_namedtuple():
    c = RGB(r=100, g=200, b=50)
    assert str(Style('x', fg=c)) == '\033[38;2;100;200;50mx\033[0m'


def test_default_no_escape_when_no_style():
    assert str(Style('plain')) == 'plain'


def test_no_color_suppresses_ansi(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    s = Style('x', fg=1)
    assert str(s) == 'x'


def test_force_color_enables_ansi(monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    with patch("sys.stdout.isatty", return_value=False):
        s = Style('x', fg=1)
    assert str(s) == '\033[31mx\033[0m'


def test_force_enable_overrides_env(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    s = Style('x', fg=1, color=Color(enable=True))
    assert str(s) == '\033[31mx\033[0m'


def test_no_color_empty_still_suppresses(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "")
    s = Style('x', fg=1)
    assert str(s) == 'x'


def test_enabled_evaluates_dynamically(monkeypatch):
    with patch("sys.stdout.isatty", return_value=True):
        s = Style('x', fg=1)
    assert str(s) == '\033[31mx\033[0m'
    with patch("sys.stdout.isatty", return_value=False):
        assert str(s) == 'x'


def test_no_color_dynamic(monkeypatch):
    s = Style('x', fg=1)
    assert str(s) == '\033[31mx\033[0m'
    monkeypatch.setenv("NO_COLOR", "1")
    assert str(s) == 'x'


def test_force_color_dynamic(monkeypatch):
    with patch("sys.stdout.isatty", return_value=False):
        s = Style('x', fg=1)
        assert str(s) == 'x'
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert str(s) == '\033[31mx\033[0m'


def test_color_tty():
    with patch("sys.stdout.isatty", return_value=True):
        assert Color.tty().enabled is True
    with patch("sys.stdout.isatty", return_value=False):
        assert Color.tty().enabled is False


def test_color_always():
    assert Color.always().enabled is True


def test_color_never():
    assert Color.never().enabled is False


def test_color_is_terminal():
    with patch("sys.stdout.isatty", return_value=True):
        assert Color().is_terminal is True
    with patch("sys.stdout.isatty", return_value=False):
        assert Color().is_terminal is False


def test_color_supports_color():
    assert Color().supports_color is True


def test_color_supports_color_notty():
    with patch("sys.stdout.isatty", return_value=False):
        assert Color().supports_color is False


def test_color_supports_color_dumb_term(monkeypatch):
    monkeypatch.setenv("TERM", "dumb")
    assert Color().supports_color is False


def test_color_supports_color_emacs_term(monkeypatch):
    monkeypatch.setenv("TERM", "emacs")
    assert Color().supports_color is False


def test_color_style_factory():
    c = Color.always()
    s = c.style("hi", fg=1)
    assert str(s) == "\033[31mhi\033[0m"


def test_color_terminal_size():
    cols, lines = Color().terminal_size()
    assert isinstance(cols, int)
    assert isinstance(lines, int)
    assert cols > 0
    assert lines > 0


def test_color_style_factory_disabled():
    c = Color.never()
    s = c.style("hi", fg=1)
    assert str(s) == "hi"
