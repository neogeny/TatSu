# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ..api import boot_grammar
from .cfg import CLIConfig
from .fmt import render_grammar
from .global_opt import add_global_options
from .grammar_cmd import add_grammar_options
from .lib import Results


def boot_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``boot`` subcommand."""

    payload = render_grammar(
        boot_grammar(),
        cfg,
        name="boot",
    )
    return [("boot", payload)]


def add_boot_cmd(subparsers):
    boot_parser = subparsers.add_parser(
        "boot",
        help="The internal boot grammar",
    )
    add_global_options(boot_parser)
    add_grammar_options(boot_parser)
    return boot_parser
