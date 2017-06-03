# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
from codecs import open
from pprint import pprint

import tatsu
from tatsu.ast import AST
from tatsu.walkers import NodeWalker

from codegen import PostfixCodeGenerator


def simple_parse():
    grammar = open('grammars/calc_cut.ebnf').read()

    parser = tatsu.compile(grammar)
    ast = parser.parse('3 + 5 * ( 10 - 20 )', trace=True, colorize=True)

    print('# SIMPLE PARSE')
    print('# AST')
    pprint(ast, width=20, indent=4)
    print()

    print('# JSON')
    print(json.dumps(ast, indent=4))
    print()


def annotated_parse():
    grammar = open('grammars/calc_annotated.ebnf').read()

    parser = tatsu.compile(grammar)
    ast = parser.parse('3 + 5 * ( 10 - 20 )')

    print('# ANNOTATED AST')
    pprint(ast, width=20, indent=4)
    print()


class CalcBasicSemantics(object):
    def number(self, ast):
        return int(ast)

    def term(self, ast):
        if not isinstance(ast, AST):
            return ast
        elif ast.op == '*':
            return ast.left * ast.right
        elif ast.op == '/':
            return ast.left / ast.right
        else:
            raise Exception('Unknown operator', ast.op)

    def expression(self, ast):
        if not isinstance(ast, AST):
            return ast
        elif ast.op == '+':
            return ast.left + ast.right
        elif ast.op == '-':
            return ast.left - ast.right
        else:
            raise Exception('Unknown operator', ast.op)


def parse_with_basic_semantics():
    grammar = open('grammars/calc_annotated.ebnf').read()

    parser = tatsu.compile(grammar)
    ast = parser.parse(
        '3 + 5 * ( 10 - 20 )',
        semantics=CalcBasicSemantics()
    )

    print('# BASIC SEMANTICS RESULT')
    pprint(ast, width=20, indent=4)
    print()


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


def parse_factored():
    grammar = open('grammars/calc_factored.ebnf').read()

    parser = tatsu.compile(grammar)
    ast = parser.parse(
        '3 + 5 * ( 10 - 20 )',
        semantics=CalcSemantics()
    )

    print('# FACTORED SEMANTICS RESULT')
    pprint(ast, width=20, indent=4)
    print()


def parse_to_model():
    grammar = open('grammars/calc_model.ebnf').read()

    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse('3 + 5 * ( 10 - 20 )')

    print('# MODEL TYPE IS:', type(model).__name__)
    print(json.dumps(model.asjson(), indent=4))
    print()


class CalcWalker(NodeWalker):
    def walk_object(self, node):
        return node

    def walk_add(self, node):
        return self.walk(node.left) + self.walk(node.right)

    def walk_subtract(self, node):
        return self.walk(node.left) - self.walk(node.right)

    def walk_multiply(self, node):
        return self.walk(node.left) * self.walk(node.right)

    def walk_divide(self, node):
        return self.walk(node.left) / self.walk(node.right)


def parse_and_walk_model():
    grammar = open('grammars/calc_model.ebnf').read()

    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse('3 + 5 * ( 10 - 20 )')

    print('# WALKER RESULT')
    print(CalcWalker().walk(model))
    print()


def parse_and_translate():
    grammar = open('grammars/calc_model.ebnf').read()

    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse('3 + 5 * ( 10 - 20 )')

    postfix = PostfixCodeGenerator().render(model)

    print('# TRANSLATED TO POSTFIX')
    print(postfix)


def main():
    simple_parse()
    annotated_parse()
    parse_with_basic_semantics()
    parse_factored()
    parse_to_model()
    parse_and_walk_model()
    parse_and_translate()


if __name__ == '__main__':
    main()
