#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import sys
from os import path

from antlr_parser import ANTLRParser as ANTLRParserBase
from tatsu.buffering import Buffer
from semantics import ANTLRSemantics

COMMENTS_RE = r'/\*(?:.|\n)*?\*/|//[^\n]*?\n'


class ANTLRParser(ANTLRParserBase):
    def parse(self, text, filename=None, **kwargs):
        return super(ANTLRParser, self).parse(text,
                                              'grammar',
                                              filename=filename,
                                              **kwargs)


def main(filename, trace):
    parser = ANTLRParser()
    with io.open(filename) as f:
        buffer = Buffer(f.read(),
                        filename=filename,
                        comments_re=COMMENTS_RE,
                        trace=True)
        gname = path.splitext(path.basename(filename))[0]
        semantics = ANTLRSemantics(gname)
        model = parser.parse(buffer,
                             filename=filename,
                             semantics=semantics,
                             trace=trace)
        print(model)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        thisprog = path.basename(sys.argv[0])
        print(thisprog)
        print('Usage:')
        print('\t', thisprog, 'FILENAME.g [--trace]')
        sys.exit(1)
    main(sys.argv[1], '--trace' in sys.argv or '-t' in sys.argv)
