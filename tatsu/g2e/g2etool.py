# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

from .. import compile, peg as g
from ..util import cast, startscript
from .semantics import ANTLRSemantics


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


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith('-') and not a.isdigit()]
    if not argv:
        thisprog = startscript()
        print(thisprog)
        print('Usage:')
        print(f'\t{thisprog} FILENAME.g [--trace] [--recursion-limit N]')
        sys.exit(1)
    filename = argv[0]
    trace = '--trace' in sys.argv or '-t' in sys.argv
    recursion_limit = _parse_recursion_limit(sys.argv)
    model = translate(
        filename=filename,
        trace=trace,
        recursion_limit=recursion_limit,
    )
    print(model.pretty())


def _parse_recursion_limit(argv: list[str]) -> int | None:
    try:
        idx = argv.index('--recursion-limit')
        if idx + 1 < len(argv):
            return int(argv[idx + 1])
    except (ValueError, IndexError):
        pass
    return None


if __name__ == '__main__':
    main()
