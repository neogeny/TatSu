# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import tatsu
from tatsu import grammars


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

    model = tatsu.compile(grammar, asmodel=True)
    assert isinstance(model, grammars.Grammar)


def test_optional():
    grammar = r"""
        start:  '['?/abc/?

        other := 'xyz'?
    """

    model = tatsu.compile(grammar, asmodel=True)
    exp = model.rulemap['start'].exp
    assert isinstance(exp, grammars.Sequence)
    assert repr(exp.sequence) == "[Token('['), Pattern(r'abc')]"

    exp = model.rulemap['other'].exp
    assert repr(exp) == "Optional(Token('xyz'))"
