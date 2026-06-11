#!/usr/bin/env python3
# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from collections import namedtuple
from copy import copy
from typing import Self

from .colormethods import ColorMethods


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

    def terminal_size(self) -> tuple[int, int]:
        """Return ``(columns, lines)`` of the terminal, falling back to 80x24."""
        import shutil

        size = shutil.get_terminal_size()
        return (size.columns, size.lines)

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


class Style(ColorMethods):
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

    def __init__(
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
        color: Color = DEFAULT_COLOR,
    ):
        self.value = value
        self._fmt: str | None = None

        self._color = color

        self._fg: int | RGB = -1
        self._bg: int | RGB = -1

        self._set_fg(fg)
        self._set_bg(bg)

        self._bold = bold
        self._dim = dim
        self._italic = italic
        self._underline = underline
        self._blink = blink
        self._inverse = inverse
        self._hidden = hidden
        self._strikethrough = strikethrough

    def __call__(self, value: str) -> Self:
        new = copy(self)
        new.value = value
        return new

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

    def apply(self, text: str) -> str:
        """Wrap *text* in ANSI escape codes according to this style.

        If ``self.enabled`` is False, returns *text* unchanged.
        If *text* is empty, returns ``""``.
        When no formatting attributes are set, returns the stored ``self.value``
        (the behaviour that powers ``__str__``).
        """
        if not text:
            return ""
        text = fmt(text, self._fmt) if self._fmt else text
        if not self.enabled:
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

    def __str__(self) -> str:
        return self.apply(self.value)

    def __repr__(self) -> str:
        return repr(str(self)).replace('\\x1b', '\\e')


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
