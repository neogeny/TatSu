# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path

from .. import compile, peg as g
from ..util import cast
from .semantics import ANTLRSemantics


__all__ = ['translate', 'add_argparse_options', 'main']


def antlr_grammar() -> str:
    path = resources.files('tatsu.g2e') / 'antlr.tatsu'
    return path.read_text()


def translate(
    text: str | None = None,
    filename: str | None = None,
    name: str | None = None,
    encoding: str = 'utf-8',
    trace: bool = False,
    recursion_limit: int | None = None,
) -> g.Grammar:
    if text is None and filename is None:
        raise ValueError('either `text` or `filename` must be provided')
    filepath = Path(filename) if filename else Path()

    if text is None:
        name = name or filepath.stem
        text = filepath.read_text(encoding=encoding)

    name = name or 'Unknown'

    if recursion_limit is not None:
        sys.setrecursionlimit(recursion_limit)

    semantics = ANTLRSemantics(name)
    grammar = compile(antlr_grammar())
    model = grammar.parse(
        text,
        name=name,
        filename=filename,
        semantics=semantics,
        trace=trace,
        colorize=True,
    )
    return cast(g.Grammar, model)


def add_g2e_cmd(subparsers) -> argparse.ArgumentParser:
    g2e_parser = subparsers.add_parser(
        "g2e",
        help="Translate ANTLR grammars to TatSu",
    )
    add_argparse_options(g2e_parser)
    return g2e_parser


def add_argparse_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "filename",
        type=Path,
        help="ANTLR grammar file to translate",
    )
    parser.add_argument(
        "-t",
        "--trace",
        action="store_true",
        help="Produce verbose parsing output",
    )
    parser.add_argument(
        "--recursion-limit",
        type=int,
        default=None,
        help="Set the Python recursion limit",
    )


def g2e_cmd(parser: argparse.ArgumentParser) -> int:
    args = parser.parse_args()

    model = translate(
        filename=str(args.filename),
        trace=args.trace,
        recursion_limit=args.recursion_limit,
    )
    print(model.pretty())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Translate ANTLR grammars to TatSu",
    )
    add_argparse_options(parser)
    return g2e_cmd(parser)


if __name__ == '__main__':
    sys.exit(main())
