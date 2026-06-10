from __future__ import annotations

from tatsu.util.colorize.style import Style


def test_default_empty():
    assert str(Style()) == ''


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


def test_fg_name():
    s = Style('x').fg_name('pink')
    assert str(s) == '\033[38;5;200mx\033[0m'


def test_bg_name():
    s = Style('x').bg_name('red')
    assert str(s) == '\033[48;5;196mx\033[0m'


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


def test_default_no_escape_when_no_style():
    assert str(Style('plain')) == 'plain'
