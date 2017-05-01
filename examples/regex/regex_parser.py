# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import model
from parser_base import RegexParser


class RegexSemantics(object):
    def __init__(self):
        super(RegexSemantics, self).__init__()
        self._count = 0

    def START(self, ast):
        return model.Regex(ast)

    def CHOICE(self, ast):
        return model.Choice(ast.opts)

    def SEQUENCE(self, ast):
        if not ast.terms:
            return model.Empty()
        elif len(ast.terms) < 2:
            return ast.terms[0]
        else:
            return model.Sequence(ast.terms)

    def CLOSURE(self, ast):
        return model.Closure(ast)

    def SUBEXP(self, ast):
        return ast

    def LITERAL(self, ast):
        return model.Literal(ast)


def translate(regex, trace=False):
    parser = RegexParser(trace=trace, semantics=RegexSemantics())
    model = parser.parse(regex, 'START')
    model.set_rule_numbers()
    return str(model.render())
