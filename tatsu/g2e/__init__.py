#!/usr/bin/env python3
from __future__ import annotations

import pkgutil
import sys
from pathlib import Path

from tatsu import compile

from .semantics import ANTLRSemantics


def antlr_grammar():
    return str(pkgutil.get_data(__name__, 'antlr.ebnf'), 'utf-8')


def translate(
    text=None, filename=None, name=None, encoding='utf-8', trace=False,
):
    if text is None and filename is None:
        raise ValueError('either `text` or `filename` must be provided')
    if filename:
        filename = Path(filename)

    if text is None:
        name = name or filename.stem
        with filename.open(encoding=encoding) as f:
            text = f.read()

    name = name or 'Unknown'

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
    print(model)


def main():
    if len(sys.argv) < 2:
        thisprog = Path(sys.argv[0]).name
        print(thisprog)
        print('Usage:')
        print('\t', thisprog, 'FILENAME.g [--trace]')
        sys.exit(1)
    translate(
        filename=sys.argv[1], trace='--trace' in sys.argv or '-t' in sys.argv,
    )


if __name__ == '__main__':
    main()
