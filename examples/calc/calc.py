import json
from pathlib import Path
from pprint import pprint

from codegen import PostfixCodeGenerator

import tatsu
from tatsu.ast import AST
from tatsu.walkers import NodeWalker


def simple_parse():
    grammar = Path('grammars/calc_cut.ebnf').read_text()

    parser = tatsu.compile(grammar)
    ast = parser.parse('3 + 5 * ( 10 - 20 )', trace=False, colorize=True)

    print()
    print('# SIMPLE PARSE')
    print('# AST')
    pprint(ast, width=20, indent=4)
    print()

    print('# JSON')
    print(json.dumps(ast, indent=4))
    print()


def annotated_parse():
    grammar = Path('grammars/calc_annotated.ebnf').read_text()

    parser = tatsu.compile(grammar)
    ast = parser.parse('3 + 5 * ( 10 - 20 )')

    print()
    print('# ANNOTATED AST')
    pprint(ast, width=20, indent=4)
    print()


class CalcBasicSemantics:
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
            raise ValueError('Unknown operator', ast.op)

    def expression(self, ast):
        if not isinstance(ast, AST):
            return ast
        elif ast.op == '+':
            return ast.left + ast.right
        elif ast.op == '-':
            return ast.left - ast.right
        else:
            raise ValueError('Unknown operator', ast.op)


def parse_with_basic_semantics():
    grammar = Path('grammars/calc_annotated.ebnf').read_text()

    parser = tatsu.compile(grammar)
    result = parser.parse(
        '3 + 5 * ( 10 - 20 )', semantics=CalcBasicSemantics(),
    )

    print()
    print('# BASIC SEMANTICS RESULT')
    assert result == -47
    print(result)
    print()


class CalcSemantics:
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
    grammar = Path('grammars/calc_factored.ebnf').read_text()

    parser = tatsu.compile(grammar)
    ast = parser.parse('3 + 5 * ( 10 - 20 )', semantics=CalcSemantics())

    print()
    print('# FACTORED SEMANTICS RESULT')
    pprint(ast, width=20, indent=4)
    print()


def parse_to_model():
    grammar = Path('grammars/calc_model.ebnf').read_text()

    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse('3 + 5 * ( 10 - 20 )')

    print()
    print('# MODEL TYPE IS:', type(model).__name__)
    print(json.dumps(model.asjson(), indent=4))
    print()


class CalcWalker(NodeWalker):
    def walk_object(self, node):
        return node

    def walk__add(self, node):
        return self.walk(node.left) + self.walk(node.right)

    def walk__subtract(self, node):
        return self.walk(node.left) - self.walk(node.right)

    def walk__multiply(self, node):
        return self.walk(node.left) * self.walk(node.right)

    def walk__divide(self, node):
        return self.walk(node.left) / self.walk(node.right)


def parse_and_walk_model():
    grammar = Path('grammars/calc_model.ebnf').read_text()

    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse('3 + 5 * ( 10 - 20 )')

    print()
    print('# WALKER RESULT')
    result = CalcWalker().walk(model)
    assert result == -47
    print(result)
    print()


def parse_and_translate():
    grammar = Path('grammars/calc_model.ebnf').read_text()

    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse('3 + 5 * ( 10 - 20 )')

    codegen = PostfixCodeGenerator()
    codegen.walk(model)
    postfix = codegen.printed_text()

    print()
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
