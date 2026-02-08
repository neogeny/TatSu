# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

from ast import parse

import pytest

from tatsu.exceptions import FailedKeywordSemantics
from tatsu.ngcodegen import pythongen
from tatsu.tool import compile


def test_keywords_in_rule_names():
    grammar = """
        start
            =
            whitespace
            ;

        whitespace
            =
                {'x'}+
            ;
    """
    m = compile(grammar, 'Keywords')
    m.parse('x')


def test_python_keywords_in_rule_names():
    # This is a regression test for
    # https://bitbucket.org/neogeny/tatsu/issues/59
    # (semantic actions not called for rules with the same name as a python
    # keyword).
    grammar = """
        not = 'x' ;
    """
    m = compile(grammar, 'Keywords')

    class Semantics:
        def __init__(self):
            self.called = False

        def not_(self, ast):
            self.called = True

    semantics = Semantics()
    m.parse('x', semantics=semantics)
    assert semantics.called


def test_define_keywords():
    grammar = """
        @@keyword :: B C
        @@keyword :: 'A'

        start = ('a' 'b').{'x'}+ ;
    """
    model = compile(grammar, 'test')
    c = pythongen(model)
    parse(c)

    grammar2 = str(model)
    model2 = compile(grammar2, 'test')
    c2 = pythongen(model2)
    parse(c2)

    assert grammar2 == str(model2)


def test_check_keywords():
    grammar = r"""
        @@keyword :: A

        start = {id}+ $ ;

        @name
        id = /\w+/ ;
    """
    model = compile(grammar, 'test')
    c = pythongen(model)
    # print(c)
    parse(c)

    ast = model.parse('hello world')
    assert ast == ['hello', 'world']

    with pytest.raises(FailedKeywordSemantics, match=r'"A" is a reserved word'):
        ast = model.parse('hello A world')


def test_check_unicode_name():
    grammar = r"""
        @@keyword :: A

        start = {id}+ $ ;

        @name
        id = /\w+/ ;
    """
    model = compile(grammar, 'test')
    model.parse('hello Øresund')


def test_sparse_keywords():
    grammar = r"""
        @@keyword :: A

        @@ignorecase :: False

        start = {id}+ $ ;

        @@keyword :: B

        @name
        id = /\w+/ ;
    """
    model = compile(grammar, 'test', trace=False, colorize=True)
    c = pythongen(model)
    parse(c)

    ast = model.parse('hello world')
    assert ast == ['hello', 'world']

    for k in ('A', 'B'):
        with pytest.raises(FailedKeywordSemantics, match=rf'"{k}" is a reserved word'):
            ast = model.parse(f'hello {k} world')
            assert ['hello', k, 'world'] == ast


def test_ignorecase_keywords():
    grammar = r"""
        @@ignorecase :: True
        @@keyword :: if

        start = rule ;

        @name
        rule = @:word if_exp $ ;

        if_exp = 'if' digit ;

        word = /\w+/ ;
        digit = /\d/ ;
    """

    model = compile(grammar, 'test')

    model.parse('nonIF if 1', trace=False)

    with pytest.raises(FailedKeywordSemantics, match=r'"IF" is a reserved word'):
        model.parse('if if 1', trace=False)

    with pytest.raises(FailedKeywordSemantics, match=r'"IF" is a reserved word'):
        model.parse('IF if 1', trace=False)


def test_keywords_are_str():
    grammar = r"""
        @@keyword :: True False

        start = $ ;
    """
    model = compile(grammar, 'test')
    assert model.keywords == ['True', 'False']
    assert all(isinstance(k, str) for k in model.keywords)
