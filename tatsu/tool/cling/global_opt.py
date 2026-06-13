# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from .config import DEFAULT_PYGMENTS_STYLE


def add_global_options(parser):
    group = parser.add_argument_group("global options")
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress bar and spinner output",
    )
    group.add_argument(
        "-vv",
        "--verbose",
        action="store_true",
        help="Provide more detailed information about the parsing process",
    )
    group.add_argument(
        "-t",
        "--trace",
        action="store_true",
        help="Display a detailed trace of the parsing process",
    )
    group.add_argument(
        "-o",
        "--output",
        default="",
        help="Output to a file or directory instead of stdout",
    )
    group.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Control colorized output (default: auto)",
    )
    group.add_argument(
        "-l",
        "--style",
        dest="style",
        default=DEFAULT_PYGMENTS_STYLE,
        help="Pygments style name for syntax highlighting",
    )
    # group.add_argument(
    #     "--profile",
    #     action="store_true",
    #     help="Enable CPU and memory profiling",
    # )
