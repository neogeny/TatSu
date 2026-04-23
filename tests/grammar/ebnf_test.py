# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import tatsu
from tatsu import grammars as g


def test_parse_ebnf():
    grammar = r"""
        /*
            Example of a grammar that mixes TatSu and EBNF
        */
        @@grammar :: TatSu  // this is TatSu wiht an EBNF comment

        start := expression $

        expression := expression '+' term | expression '-' term | term

        term := term '*' factor | term '/' factor | factor

        factor := '(' expression ')' | number

        number := /\d+/
    """

    model = tatsu.compile_to_parser(grammar)
    assert isinstance(model, g.Grammar)


def test_optional():
    grammar = r"""
        start:  '[' /abc/

        other := 'xyz'?
    """

    model = tatsu.compile_to_parser(grammar)
    exp = model.rulemap['start'].exp
    assert isinstance(exp, g.Sequence)
    assert repr(exp.sequence) == "[Token('['), Pattern('abc')]"

    exp = model.rulemap['other'].exp
    assert repr(exp) == "Optional(Token('xyz'))"


def test_one_line_grammar():
    grammar = r"""
            start: lisp

            lisp: sexp | list | symbol

            sexp[SExp]: '(' cons=lisp '.' ~ cdr=lisp ')'

            list[List]: '(' ={lisp} ')'

            symbol[Symbol]: /[^\s().]+/

        """

    one_line_grammar = ' ; '.join(s for s in grammar.splitlines() if s.strip())
    parser = tatsu.compile(one_line_grammar)
    model = parser.parse("( abc (x . y))", asmodel=True)
    # FIXME: the order of arguments should be stable in NodeBase.__repr__
    assert repr(model) in {
        "List(Symbol('abc'), SExp(cons=Symbol('x'), cdr=Symbol('y')))",
        "List(Symbol('abc'), SExp(cdr=Symbol('y'), cons=Symbol('x')))",
    }
