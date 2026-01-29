from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

from .. import compile, grammars
from .semantics import ANTLRSemantics


def antlr_grammar() -> str:
    path = resources.files('tatsu.g2e') / 'antlr.ebnf'
    return path.read_text()


def translate(
        text: str | None = None,
        filename: str | None = None,
        name: str | None = None,
        encoding: str = 'utf-8',
        trace: bool = False,
) -> grammars.Grammar:
    if text is None and filename is None:
        raise ValueError('either `text` or `filename` must be provided')
    if filename:
        filepath = Path(filename)

    if text is None:
        name = name or filepath.stem
        text = filepath.read_text(encoding=encoding)

    name = name or 'Unknown'

    semantics = ANTLRSemantics(name)
    grammar = compile(antlr_grammar())
    return grammar.parse(
        text,
        name=name,
        filename=filename,
        semantics=semantics,
        trace=trace,
        colorize=True,
    )


def main():
    if len(sys.argv) < 2:
        thisprog = Path(sys.argv[0]).name
        print(thisprog)
        print('Usage:')
        print('\t', thisprog, 'FILENAME.g [--trace]')
        sys.exit(1)
    model = translate(
        filename=sys.argv[1], trace='--trace' in sys.argv or '-t' in sys.argv,
    )
    print(model)


if __name__ == '__main__':
    main()
