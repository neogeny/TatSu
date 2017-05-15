#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals  # noqa

import codecs
import sys
import pkgutil
from os import path

from tatsu import parse
from .semantics import ANTLRSemantics


def antlr_grammar():
    return str(pkgutil.get_data(__name__, 'antlr.ebnf'), 'utf-8')


def translate(text=None, filename=None, name=None, encoding='utf-8', trace=False):
    if text is None and filename is None:
        raise ValueError('either `text` or `filename` must be provided')

    if text is None:
        name = name or path.splitext(path.basename(filename))[0].capitalize()
        with codecs.open(filename, encoding=encoding) as f:
            text = f.read()

    name = name or 'Unknown'

    semantics = ANTLRSemantics(name)
    model = parse(
        antlr_grammar(),
        text,
        name=name,
        filename=filename,
        semantics=semantics,
        trace=trace
    )
    print(model)


def main():
    if len(sys.argv) < 2:
        thisprog = path.basename(sys.argv[0])
        print(thisprog)
        print('Usage:')
        print('\t', thisprog, 'FILENAME.g [--trace]')
        sys.exit(1)
    translate(
        filename=sys.argv[1],
        trace='--trace' in sys.argv or '-t' in sys.argv
    )


if __name__ == '__main__':
    main()
