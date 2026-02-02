from __future__ import annotations

import json  # noqa: F401
from typing import Any

import pytest

import tatsu
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
