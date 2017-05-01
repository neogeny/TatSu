# -*- coding: utf-8 -*-
# this is calc.py
from __future__ import print_function
import sys
from calc_parser import CalcParser


class CalcSemantics(object):
    def number(self, ast):
        return int(ast)

    def factor(self, ast):
        if not isinstance(ast, list):
            return ast
        else:
            return ast[1]

    def term(self, ast):
        if not isinstance(ast, list):
            return ast
        elif ast[1] == '*':
            return ast[0] * ast[2]
        elif ast[1] == '/':
            return ast[0] / ast[2]
        else:
            raise Exception('Unknown operator', ast[1])

    def expression(self, ast):
        if not isinstance(ast, list):
            return ast
        elif ast[1] == '+':
            return ast[0] + ast[2]
        elif ast[1] == '-':
            return ast[0] - ast[2]
        else:
            raise Exception('Unknown operator', ast[1])


def calc(text):
    parser = CalcParser(semantics=CalcSemantics())
    return parser.parse(text)


if __name__ == '__main__':
    text = open(sys.argv[1]).read()
    result = calc(text)
    print(text.strip(), '=', result)
