# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json  # noqa: F401
from typing import Any

import pytest

import tatsu
from tatsu import grammars
from tatsu.objectmodel import Node


def test_node_kwargs() -> None:
    class Atom(Node):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        arguments: Any = None
        symbol: Any = None

    atom = Atom(symbol='foo')
    assert type(atom).__name__ == 'Atom'
    assert atom.ast is None
    assert atom.symbol == 'foo'

    atom = Atom(symbol='foo', ast={})
    assert atom.ast == {}
    assert atom.symbol is not None
    assert atom.symbol == 'foo'

    atom = Atom(ast=42, symbol='foo')
    assert atom.ast == 42
    assert atom.symbol is not None
    assert atom.symbol == 'foo'

    atom = Atom(ast={'bar': 1}, symbol='foo')
    assert atom.ast == {'bar': 1}

    with pytest.warns(
            UserWarning,
            match=r'children.*?in keyword arguments will shadow.*?Atom\.children',
    ):
        atom = Atom(children=[])
        assert atom


def test_children():
    grammar = r"""
        @@grammar::Calc


        start
            =
            expression $
            ;


        expression
            =
            | add:addition
            | sub:subtraction
            | term:term
            ;


        addition::Add
            =
            left:term op:'+' ~ right:expression
            ;


        subtraction::Subtract
            =
            left:term op:'-' ~ right:expression
            ;


        term
            =
            | mul:multiplication
            | div:division
            | factor:factor
            ;


        multiplication::Multiply
            =
            left:factor op:'*' ~ right:term
            ;


        division::Divide
            =
            left:factor '/' ~ right:term
            ;


        factor
            =
            | subexpression
            | number
            ;


        subexpression
            =
            '(' ~ @:expression ')'
            ;


        number::int
            =
            /\d+/
            ;
    """

    parser = tatsu.compile(grammar, asmodel=True, trace=False)
    assert parser
    model = parser.parse('3 + 5 * ( 10 - 20 )')
    assert model
    assert model['add']
    assert model['add'].children()
    assert type(model['add'].children()[0]).__name__ == 'Multiply'


def test_model_repr():
    node = Node()
    assert repr(node) == 'Node()'

    node = Node('hello')
    assert repr(node) == "Node(ast='hello')"

    node = Node(ast='hello')
    assert repr(node) == "Node(ast='hello')"

    node = Node(ast='hello', ctx='world')
    assert repr(node) == "Node(ast='hello')"

    with pytest.raises(ValueError, match=r'world='):
        Node(ast='hello', world='world')

    token = grammars.Token(ast='hello')
    assert repr(token) == "Token(token='hello')"

    token = grammars.Token(token='hello')
    assert repr(token) == "Token(token='hello')"

    with pytest.raises(TypeError, match=r'1 positional argument'):
        grammars.Token('hello')

    with pytest.raises(TypeError, match=r'unexpected keyword argument'):
        grammars.Token(x='x')

    with pytest.raises(TypeError, match=r'name is required'):
        grammars.Named()

    named = grammars.Named(name='foo')
    assert repr(named) == "Named(name='foo')"

    named = grammars.Named(name='foo', ast='bar')
    assert repr(named) == "Named(exp='bar', name='foo')"

    named = grammars.Named(name='foo', exp='bar')
    assert repr(named) == "Named(exp='bar', name='foo')"
