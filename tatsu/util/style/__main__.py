# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
"""
Visual verification tables for the ANSI colour library.

.. code-block:: text

    python -m tatsu.util.colorize

Displays the 16x16 ANSI colour cube, the named colour palette,
dynamic colour-method tests, and the CSS named colour table.
"""

from __future__ import annotations

from pathlib import Path

from .colormap import COLORMAP
from .csscolormap import CSS_COLORS
from .style import Style


def main():
    """Print all verification tables to stdout."""
    print_color_table()
    print_colormap_table()
    print_color_method_table()
    print_css_color_table()
    # add_color_methods()

    print(
        f'{Style(value="A pink", fg=200)} and {Style(value="a magenta", fg=201)} {Style(value="aquamarine", fg=72)} world'
    )


def col_header(row: int, width: int = 4):
    """Print a row-number header cell, right-aligned in *width* columns."""
    print(f'{row if row >= 0 else "":>{width}}', end=" ")


def header(width: int = 4):
    """Print the 16-column colour-table header."""
    col_header(-1, width)
    for col in range(16):
        print(f'{col:>{width}d}', end=" ")


def print_color_table():
    """Print the 16x16 ANSI colour cube (0-255) as a grid."""
    header()
    for row in range(16):
        col_header(row, 4)
        for col in range(16):
            index = row * 16 + col
            print(Style(value=f'{index:>3d}', fg=index), end=" ")
        print()
    print()


def print_colormap_table():
    """Print all named ANSI colours in their own foreground colour."""
    width = 24
    k = 100 // width
    for n, name in enumerate(COLORMAP.keys()):
        col = n % k
        if col == 0:
            print()
        print(Style(value=f'{name:>{width}s}', fg=COLORMAP[name]), end=" ")
    print()
    print()


def print_color_method_table():
    """Print the dynamic colour-method names in their own foreground."""
    width = 24
    k = 100 // width
    n = 0
    for n, name in enumerate(COLORMAP):
        style = Style(f'{name:>{width}s}')
        m = getattr(style, name.replace(' ', '_'), None)
        if m is not None:
            style = m()

        col = n % k
        if col == 0:
            print()
        print(style, end=" ")
    print()
    print()


def print_css_color_table():
    """Print all CSS named colours swatched in their own foreground."""
    width = 24
    k = 100 // width
    for n, (name, rgb) in enumerate(CSS_COLORS.items()):
        col = n % k
        if col == 0:
            print()
        swatch = Style(value=f'{name:>{width}s}', fg=rgb)
        print(swatch, end=" ")
    print()
    print()


def add_color_methods():
    cls = Style
    with Path("./methods.py").open("tw+") as f:
        for name, code in COLORMAP.items():
            method_name = name.replace(' ', '_')
            if hasattr(Style, method_name):
                continue

            def _color_method(self, s: str = "", code: int = code) -> Style:
                return type(self)(value=s, fg=code)

            setattr(
                cls,
                method_name,
                _color_method,
            )

    with Path("./methods.py").open("tw+") as f:
        for name, code in sorted(COLORMAP.items()):
            method_name = name.replace(' ', '_')
            f.write(f'    def {method_name}(self) -> Self:\n')
            f.write(f'        return self.fg({code})\n')
            f.write('\n')

            f.write(f'    def {method_name}_bg(self) -> Self:\n')
            f.write(f'        return self.bg({code})\n')
            f.write('\n')

            f.flush()


if __name__ == "__main__":
    main()
