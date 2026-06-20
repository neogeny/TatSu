# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
ANSI terminal colour — zero dependencies, optionally self-contained.

Provides a ``Color`` policy object and a ``Style`` composer for building
ANSI-wrapped terminal text.  Supports 256-colour palettes, 24-bit RGB,
148 CSS named colours, dynamic TTY detection, ``NO_COLOR`` / ``FORCE_COLOR``
environment variables, and lazy-loading colour maps.

Quick-start:

.. code-block:: python

    from tatsu.util.style import Color, Style

    style = Style("hello", bold=True, fg=2, color=Color.tty())
    print(style)  # ANSI-wrapped on TTY, plain text otherwise
"""

from __future__ import annotations

from .colormap import *  # noqa: F403
from .csscolormap import *  # noqa: F403
from .style import *  # noqa: F403
from .style import (
    RGB,
    Color,
    Style,
    css_color,
    fmt,
    named_color,
    rgb,
    visual_len,
)


__all__ = [
    "Color",
    "RGB",
    "Style",
    "css_color",
    "fmt",
    "named_color",
    "rgb",
    "visual_len",
]
