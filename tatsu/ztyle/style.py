# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import contextlib
import inspect
import os
import re
from collections import namedtuple
from collections.abc import Callable
from copy import copy
from typing import Any, Self

from ..util.tty import ANSI_RE, SGR_RE, tty_escape, tty_unescape, visual_len


class RGB(namedtuple('RGB', ['r', 'g', 'b'])):
    """A 24-bit RGB color tuple with 0-255 byte clamping.

    Usage:
        RGB(255, 0, 0)  # pure red
        rgb(128, 128, 128)  # via the rgb() helper
    """

    __slots__ = ()

    def __new__(cls, r: int, g: int, b: int) -> Self:
        def to_byte(v: int) -> int:
            return max(0, min(v, 255))

        return super().__new__(cls, to_byte(r), to_byte(g), to_byte(b))


def rgb(r: int, g: int, b: int) -> RGB:
    """Create an RGB tuple from 0-255 byte values."""
    return RGB(r, g, b)


class Color:
    """Policy object controlling whether ANSI color codes are emitted.

    Color evaluates three sources in priority order:
        1. An explicit enable override (set via the constructor or ``.enable()``).
        2. The ``NO_COLOR`` environment variable (disables color when set).
        3. The ``FORCE_COLOR`` environment variable (enables color when set).
        4. Whether ``sys.stdout`` is a TTY (the default heuristic).

    Factory methods:
        ``Color.tty()`` — deference to the TTY check (the default).
        ``Color.always()`` — always emit color.
        ``Color.never()`` — never emit color.
        ``Color.default()`` — same as ``Color()``; self-documenting alias.

    Use ``Color.style(...)`` to create a ``Style`` bound to this policy,
    or pass as ``color=`` to the ``Style`` constructor.
    """

    def __init__(self, enable: bool | None = None):
        self._force_enable: bool | None = enable
        self._check_stderr: bool = False

    def enable(self, value: bool) -> None:
        """Override the enable policy with an explicit boolean.

        After calling ``.enable(False)``, all ``Style`` instances using this
        ``Color`` will return plain text.  Useful to turn color off globally
        based on a CLI flag:

            Color.default().enable(args.no_color)
        """
        self._force_enable = value

    def markup(self, text: str):
        from .markup import markup

        return markup(text, color=self)

    def style(
        self,
        value: str = "",
        *,
        fg: int | RGB | None = -1,
        bg: int | RGB | None = -1,
        bold: bool = False,
        dim: bool = False,
        italic: bool = False,
        underline: bool = False,
        blink: bool = False,
        inverse: bool = False,
        hidden: bool = False,
        strikethrough: bool = False,
    ) -> Style:
        """Create a ``Style`` bound to this color policy.

        All keyword arguments are forwarded to ``Style.__init__``.
        """
        return Style(
            value,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            italic=italic,
            underline=underline,
            blink=blink,
            inverse=inverse,
            hidden=hidden,
            strikethrough=strikethrough,
            color=self,
        )

    @classmethod
    def tty(cls) -> Color:
        """Create a Color that defers to TTY detection (default)."""
        return cls()

    @classmethod
    def always(cls) -> Color:
        """Create a Color that always emits ANSI codes."""
        return cls(enable=True)

    @classmethod
    def never(cls) -> Color:
        """Create a Color that never emits ANSI codes."""
        return cls(enable=False)

    @classmethod
    def default(cls) -> Color:
        """Return the system default Color (TTY-dependent, env-observing)."""
        return cls()

    @classmethod
    def stderr(cls) -> Color:
        """Create a Color that checks ``sys.stderr`` instead of ``sys.stdout``.

        Useful for rendering error messages, which typically go to stderr.
        Respects ``NO_COLOR`` / ``FORCE_COLOR`` normally.
        """
        c = cls()
        c._check_stderr = True
        return c

    @property
    def is_terminal(self) -> bool:
        """True if the configured stream is connected to a terminal.

        By default checks ``sys.stdout``; ``Color.stderr()`` checks
        ``sys.stderr`` instead.
        """
        import sys

        stream = sys.stderr if self._check_stderr else sys.stdout
        return stream.isatty()

    @staticmethod
    def terminal_size() -> os.terminal_size:
        """Return ``(columns, lines)`` of the terminal, falling back to 80x24."""
        import shutil

        return shutil.get_terminal_size()

    @property
    def supports_color(self) -> bool:
        """True if the terminal is capable of ANSI color (independent of policy).

        Checks TTY, ``TERM`` (not dumb/emacs), and terminal width.
        Does NOT check ``NO_COLOR``/``FORCE_COLOR`` — see ``enabled`` for that.
        """
        import os
        import shutil
        import sys

        if not sys.stdout.isatty():
            return False
        if os.environ.get("TERM", "") in {"dumb", "emacs"}:
            return False
        try:
            size = shutil.get_terminal_size()
            if size.columns < 1:
                return False
        except (ValueError, OSError):
            return False
        return True

    @property
    def enabled(self) -> bool:
        """Whether color should be emitted, evaluating policy in priority order:

        1. Explicit ``enable()`` override.
        2. ``NO_COLOR`` env var → disabled.
        3. ``FORCE_COLOR`` env var → enabled.
        4. ``sys.stdout.isatty()``.
        """
        import os

        if self._force_enable is not None:
            return self._force_enable
        if os.environ.get("NO_COLOR") is not None:
            return False
        if os.environ.get("FORCE_COLOR") is not None:
            return True
        return self.is_terminal


DEFAULT_COLOR: Color = Color.default()


class Style(str):
    """A composable ANSI style builder.

    ``Style`` stores a text *value* plus formatting attributes (foreground
    color, background color, bold, dim, italic, …).  All modifier methods
    return a **copy** so styles are immutable and chainable:

    .. code-block:: python

        s = Style("hello", bold=True, fg=2)
        str(s)  # → "\\033[1;32mhello\\033[0m"

    When ``color.enabled`` is False, ``str()`` and ``apply()`` return the
    plain text unchanged — no ANSI codes leak into pipes, logs, or CI output.

    Most modifier methods accept a ``None`` or ``-1`` fg/bg to unset
    a previously assigned color, and ``RGB`` for 24-bit color.
    """

    __slots__ = (
        "_bg",
        "_blink",
        "_bold",
        "_color",
        "_dim",
        "_fg",
        "_fmt",
        "_hidden",
        "_inverse",
        "_italic",
        "_strikethrough",
        "_underline",
    )

    def __json__(self, seen: set[int] | None = None) -> Any:
        return repr(self)

    def markup(self, text: str):
        from .markup import markup

        return markup(text, color=self.color)

    @property
    def value(self) -> str:
        return super().__str__()

    @property
    def color(self) -> Color:
        return self._color

    @classmethod
    def tty_escape(cls, text: str) -> str:
        return tty_escape(text)

    @classmethod
    def tty_unescape(cls, text: str) -> str:
        return tty_unescape(text)

    @classmethod
    def is_style_method(cls, name: str) -> bool:
        meth: Callable[[], Self] | None = None
        if (meth := getattr(cls, name, None)) is None or not callable(meth):
            return False
        sig = inspect.signature(meth)
        if str(sig.return_annotation) not in {"Style", "Self"}:
            return False
        with contextlib.suppress(TypeError):
            sig.bind(None)
            return True
        return False

    def get_style_method(self, name: str) -> Callable[[], Self] | None:
        if not self.is_style_method(name):
            return None
        return getattr(self, name, None)

    @classmethod
    def list_style_methods(cls) -> list[str]:
        return [name for name in dir(cls) if cls.is_style_method(name)]

    def __new__(cls, *args, **_kwargs):
        return super().__new__(cls, *args)

    def __str__(self) -> str:
        return self.apply(self.value)

    def __format__(self, format_spec: str) -> str:
        return self.apply(str(self), fmt=format_spec)

    def __repr__(self) -> str:
        text = self.value
        if self._fmt is not None:
            # NOTE Meant for Style.parse() not for f-strings
            text = f"f{{{self.value}:{self._fmt}}}"
        text = self.apply_style(text, force=True)
        return tty_escape(repr(text)[1:-1])

    def __len__(self) -> int:
        return visual_len(str(self))

    def __hash__(self) -> int:
        return hash(self.__dict__)

    def __eq__(self, other: object) -> bool:
        if not hasattr(other, "__dict__"):
            return False
        return self.__dict__ == other.__dict__

    def __init__(
        self,
        value: str = "",
        /,
        *,
        fmt: str | None = None,
        fg: int | RGB | None = -1,
        bg: int | RGB | None = -1,
        bold: bool = False,
        dim: bool = False,
        italic: bool = False,
        underline: bool = False,
        blink: bool = False,
        inverse: bool = False,
        hidden: bool = False,
        strikethrough: bool = False,
        color: Color = DEFAULT_COLOR,
        **_kwargs,
    ):
        super().__init__()
        _ = value

        self._color = color

        self._fg: int | RGB = -1
        self._bg: int | RGB = -1

        self._set_fg(fg)
        self._set_bg(bg)

        self._fmt = fmt
        self._bold = bold
        self._dim = dim
        self._italic = italic
        self._underline = underline
        self._blink = blink
        self._inverse = inverse
        self._hidden = hidden
        self._strikethrough = strikethrough

    def _kwattrs(self) -> dict[str, Any]:
        return {k.lstrip('_'): getattr(self, k, None) for k in type(self).__slots__}

    def __call__(self, value: str, /, *, fmt: str | None = None) -> Self:
        kw = self._kwattrs()
        kw.pop('value', None)
        if fmt is not None:
            kw['fmt'] = fmt
        return type(self)(value, **kw)

    @property
    def enabled(self) -> bool:
        """Whether this style emits ANSI codes, delegated to the bound ``Color``."""
        return self._color.enabled

    def _set_fg(self, value: int | RGB | None) -> None:
        if isinstance(value, RGB):
            self._fg = value
        elif value is None or value < 0:
            self._fg = -1
        else:
            self._fg = max(0, min(value, 255))

    def _set_bg(self, value: int | RGB | None) -> None:
        if isinstance(value, RGB):
            self._bg = value
        elif value is None or value < 0:
            self._bg = -1
        else:
            self._bg = max(0, min(value, 255))

    def fg_name(self, name: str) -> Self:
        """Set foreground to a named ANSI color (e.g. ``"red"``, ``"bright_green"``).

        The color name is matched case-insensitively, with spaces removed.
        This loads the color map lazily on first call.
        """
        from .colormap import color

        new = copy(self)
        new._set_fg(color(name))
        return new

    def bg_name(self, name: str) -> Self:
        """Set background to a named ANSI color (e.g. ``"navy"``, ``"teal"``).

        Like ``fg_name``, the color map loads lazily.
        """
        from .colormap import color

        new = copy(self)
        new._set_bg(color(name))
        return new

    def fg_css(self, name: str) -> Self:
        """Set foreground to a CSS named color (e.g. ``"rebeccapurple"``).

        Uses the 148 CSS named colors.  Loads lazily on first call.
        """
        from .csscolormap import css_color

        new = copy(self)
        rgb = css_color(name)
        if rgb is not None:
            new._set_fg(rgb)
        return new

    def bg_css(self, name: str) -> Self:
        """Set background to a CSS named color (e.g. ``"lightseagreen"``)."""
        from .csscolormap import css_color

        new = copy(self)
        rgb = css_color(name)
        if rgb is not None:
            new._set_bg(rgb)
        return new

    def fg(self, value: int | RGB | None) -> Self:
        """Set foreground to an ANSI 256-color index (0-255) or RGB.

        Pass ``None`` to reset the foreground color.
        """
        new = copy(self)
        new._set_fg(value)
        return new

    def bg(self, value: int | RGB | None) -> Self:
        """Set background to an ANSI 256-color index (0-255) or RGB.

        Pass ``None`` to reset the background color.
        """
        new = copy(self)
        new._set_bg(value)
        return new

    def fg_rgb(self, r: int, g: int, b: int) -> Self:
        """Set foreground to a 24-bit RGB color."""
        new = copy(self)
        new._set_fg(rgb(r, g, b))
        return new

    def bg_rgb(self, r: int, g: int, b: int) -> Self:
        """Set background to a 24-bit RGB color."""
        new = copy(self)
        new._set_bg(rgb(r, g, b))
        return new

    # ANSI standard colors (0-7)

    def black(self) -> Self:
        return self.fg(0)

    def black_bg(self) -> Self:
        return self.bg(0)

    def red(self) -> Self:
        return self.fg(1)

    def red_bg(self) -> Self:
        return self.bg(1)

    def green(self) -> Self:
        return self.fg(2)

    def green_bg(self) -> Self:
        return self.bg(2)

    def yellow(self) -> Self:
        return self.fg(3)

    def yellow_bg(self) -> Self:
        return self.bg(3)

    def blue(self) -> Self:
        return self.fg(4)

    def blue_bg(self) -> Self:
        return self.bg(4)

    def purple(self) -> Self:
        return self.fg(5)

    def purple_bg(self) -> Self:
        return self.bg(5)

    def magenta(self) -> Self:
        return self.purple()

    def cyan(self) -> Self:
        return self.fg(6)

    def cyan_bg(self) -> Self:
        return self.bg(6)

    def white(self) -> Self:
        return self.fg(7)

    def white_bg(self) -> Self:
        return self.bg(7)

    # ANSI bright colors (8-15)

    def bright_black(self) -> Self:
        return self.fg(8)

    def bright_black_bg(self) -> Self:
        return self.bg(8)

    def bright_red(self) -> Self:
        return self.fg(9)

    def bright_red_bg(self) -> Self:
        return self.bg(9)

    def bright_green(self) -> Self:
        return self.fg(10)

    def bright_green_bg(self) -> Self:
        return self.bg(10)

    def bright_yellow(self) -> Self:
        return self.fg(11)

    def bright_yellow_bg(self) -> Self:
        return self.bg(11)

    def bright_blue(self) -> Self:
        return self.fg(12)

    def bright_blue_bg(self) -> Self:
        return self.bg(12)

    def bright_purple(self) -> Self:
        return self.fg(13)

    def bright_purple_bg(self) -> Self:
        return self.bg(13)

    def bright_magenta(self) -> Self:
        return self.bright_purple()

    def bright_cyan(self) -> Self:
        return self.fg(14)

    def bright_cyan_bg(self) -> Self:
        return self.bg(14)

    def bright_white(self) -> Self:
        return self.fg(15)

    def bright_white_bg(self) -> Self:
        return self.bg(15)

    def bold(self) -> Self:
        """Add bold (SGR 1)."""
        new = copy(self)
        new._bold = True
        return new

    def bright(self) -> Self:
        """Add bright (SGR 1)."""
        return self.bold()

    def dim(self) -> Self:
        """Add dim/faint (SGR 2)."""
        new = copy(self)
        new._dim = True
        return new

    def italic(self) -> Self:
        """Add italic (SGR 3)."""
        new = copy(self)
        new._italic = True
        return new

    def underline(self) -> Self:
        """Add underline (SGR 4)."""
        new = copy(self)
        new._underline = True
        return new

    def blink(self) -> Self:
        """Add slow blink (SGR 5)."""
        new = copy(self)
        new._blink = True
        return new

    def inverse(self) -> Self:
        """Swap foreground and background colors (SGR 7)."""
        new = copy(self)
        new._inverse = True
        return new

    def hidden(self) -> Self:
        """Hide text / make invisible (SGR 8)."""
        new = copy(self)
        new._hidden = True
        return new

    def strikethrough(self) -> Self:
        """Add strikethrough / crossed-out (SGR 9)."""
        new = copy(self)
        new._strikethrough = True
        return new

    def fmt(self, fmt_spec: str) -> Self:
        """Set a format specification (a style will still create a copy)."""
        new = copy(self)
        new._fmt = fmt_spec
        return new

    def apply(self, text: str, fmt: str | None = None) -> str:
        """Wrap *text* in ANSI escape codes according to this style.

        If ``self.enabled`` is False, returns *text* unchanged.
        If *text* is empty, returns ``""``.
        When no formatting attributes are set, returns the stored ``self.value``
        (the behaviour that powers ``__str__``).
        """
        if not text:
            return ""
        if not fmt:
            fmt = self._fmt
        text = format(text, fmt) if fmt else text
        return self.apply_style(text)

    def apply_style(self, text: str, force: bool = False) -> str:
        if not text:
            return ""
        if not (self.enabled or force):
            return text
        codes: list[str] = []
        if self._bold:
            codes.append('1')
        if self._dim:
            codes.append('2')
        if self._italic:
            codes.append('3')
        if self._underline:
            codes.append('4')
        if self._blink:
            codes.append('5')
        if self._inverse:
            codes.append('7')
        if self._hidden:
            codes.append('8')
        if self._strikethrough:
            codes.append('9')
        if isinstance(self._fg, RGB):
            codes.append(f'38;2;{self._fg.r};{self._fg.g};{self._fg.b}')
        elif self._fg != -1:
            c = self._fg
            if c < 8:
                codes.append(str(30 + c))
            elif c < 16:
                codes.append(str(90 + c - 8))
            else:
                codes.append(f'38;5;{c}')
        if isinstance(self._bg, RGB):
            codes.append(f'48;2;{self._bg.r};{self._bg.g};{self._bg.b}')
        elif self._bg != -1:
            c = self._bg
            if c < 8:
                codes.append(str(40 + c))
            elif c < 16:
                codes.append(str(100 + c - 8))
            else:
                codes.append(f'48;5;{c}')
        if not codes:
            return text
        return f"\033[{';'.join(codes)}m{text}\033[0m"

    @classmethod
    def from_raw(cls, text: str) -> Self:
        text = tty_unescape(text)

        sgr = SGR_RE.search(text)
        if not sgr:
            return cls.parse_fmt(text)

        text_content = ANSI_RE.sub("", text)
        params_str = sgr.group(1)

        fg: int | RGB = -1
        bg: int | RGB = -1
        bold = dim = italic = underline = blink = inverse = hidden = strikethrough = (
            False
        )

        if params_str:
            params = [int(p) for p in params_str.split(";")]
            i = 0
            while i < len(params):
                p = params[i]
                if p == 0:
                    pass
                elif p == 1:
                    bold = True
                elif p == 2:
                    dim = True
                elif p == 3:
                    italic = True
                elif p == 4:
                    underline = True
                elif p == 5:
                    blink = True
                elif p == 7:
                    inverse = True
                elif p == 8:
                    hidden = True
                elif p == 9:
                    strikethrough = True
                elif 30 <= p <= 37:
                    fg = p - 30
                elif 40 <= p <= 47:
                    bg = p - 40
                elif p == 38:
                    if i + 1 < len(params):
                        if params[i + 1] == 5 and i + 2 < len(params):
                            fg = params[i + 2]
                            i += 2
                        elif params[i + 1] == 2 and i + 4 < len(params):
                            fg = RGB(params[i + 2], params[i + 3], params[i + 4])
                            i += 4
                elif p == 48:
                    if i + 1 < len(params):
                        if params[i + 1] == 5 and i + 2 < len(params):
                            bg = params[i + 2]
                            i += 2
                        elif params[i + 1] == 2 and i + 4 < len(params):
                            bg = RGB(params[i + 2], params[i + 3], params[i + 4])
                            i += 4
                elif 90 <= p <= 97:
                    fg = p - 82
                elif 100 <= p <= 107:
                    bg = p - 92
                i += 1

        kwargs: dict[str, Any] = {}
        if fg != -1:
            kwargs["fg"] = fg
        if bg != -1:
            kwargs["bg"] = bg
        if bold:
            kwargs["bold"] = True
        if dim:
            kwargs["dim"] = True
        if italic:
            kwargs["italic"] = True
        if underline:
            kwargs["underline"] = True
        if blink:
            kwargs["blink"] = True
        if inverse:
            kwargs["inverse"] = True
        if hidden:
            kwargs["hidden"] = True
        if strikethrough:
            kwargs["strikethrough"] = True

        return cls.parse_fmt(text_content, **kwargs)

    @classmethod
    def parse_fmt(cls, text: str, **kwargs) -> Self:
        fmt = None
        if m := re.match(r"f{(.*?):(.*)}", text):
            text, fmt = m.group(1, 2)
        return cls(text, color=Color.default(), fmt=fmt, **kwargs)


def named_color(name: str) -> int | None:
    """Look up a named ANSI color code (0-255) by name.

    The color name is matched case-insensitively, with spaces removed.
    Returns the ANSI 256-color index or ``None`` if unknown.
    The color-map module is loaded lazily.
    """
    from .colormap import color

    return color(name)


def css_color(name: str) -> RGB | None:
    """Look up a CSS named color as an ``RGB`` tuple.

    Accepts standard CSS color names like ``"rebeccapurple"``,
    ``"mediumseagreen"``, etc.  Returns ``None`` for unknown names.
    The CSS color map is loaded lazily.
    """
    from .csscolormap import css_color

    return css_color(name)


def fmt(value: str, fmt: str) -> str:
    """Format *value* according to the Python format specification *fmt*.

    Wraps ``f'{value:{fmt}}'`` with exception handling so invalid
    format specs degrade gracefully to the original value.

    Example:
        fmt("hello", ">10")  # "     hello"
        fmt("hello", ".2")   # "he"
    """
    if not fmt:
        return value
    try:
        return f'{value:{fmt}}'
    except (ValueError, TypeError):
        return value
