# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from pathlib import Path

from .cfg import CLIConfig
from .fmt import render_grammar
from .global_opt import add_global_options
from .grammar_opt import add_grammar_options
from .lib import Results, load_grammar


def add_grammar_cmd(subparsers):
    grammar_parser = subparsers.add_parser(
        "grammar",
        help="Grammar transformations",
        add_help=True,
    )
    add_global_options(grammar_parser)
    add_grammar_options(grammar_parser)
    grammar_parser.add_argument(
        "grammar", help="Path to the grammar source (.ebnf or .json)"
    )
    return grammar_parser


def grammar_cmd(cfg: CLIConfig) -> Results:
    """Handle the ``grammar`` subcommand."""
    if cfg.grammar is None:
        raise ValueError("expected a grammar path")
    path = cfg.grammar
    if not Path(path).is_file():
        raise ValueError(f"expected a grammar file, got {path}")
    grammar = load_grammar(path)

    payload = render_grammar(
        grammar,
        cfg,
        name=Path(path).stem,
    )
    return [(str(path), payload)]
