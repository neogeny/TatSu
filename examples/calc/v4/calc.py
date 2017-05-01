# -*- coding: utf-8 -*-
# this is calc.py
from __future__ import print_function
import sys
from calc_parser import CalcParser


class CalcSemantics(object):
    def number(self, ast):
        return int(ast)

    def addition(self, ast):
        return ast.left + ast.right

    def subtraction(self, ast):
        return ast.left - ast.right

    def multiplication(self, ast):
        return ast.left * ast.right

    def division(self, ast):
        return ast.left / ast.right


def calc(text):
    parser = CalcParser(semantics=CalcSemantics())
    return parser.parse(text)


if __name__ == '__main__':
    text = open(sys.argv[1]).read()
    result = calc(text)
    print(text.strip(), '=', result)
