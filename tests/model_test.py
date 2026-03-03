# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json  # noqa: F401
from typing import Any

import pytest

import tatsu
from tatsu import grammars as g
from tatsu.objectmodel import Node
from tatsu.util.string import prints, trim


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

    with pytest.raises(TypeError, match=r'Overriding method children'):
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

    token = g.Token(ast='hello')
    assert repr(token) == "Token(token='hello')"

    token = g.Token(token='hello')
    assert repr(token) == "Token(token='hello')"

    g.Token('hello')
    assert repr(token) == "Token(token='hello')"

    with pytest.raises(TypeError, match=r'unexpected keyword argument'):
        g.Token(x='x')

    with pytest.raises(TypeError, match=r'name is required'):
        g.Named()

    named = g.Named(name='foo')
    assert repr(named) == "Named(name='foo', exp=Void())"

    named = g.Named(name='foo', ast='bar')
    assert repr(named) == "Named(name='foo', exp='bar')"

    named = g.Named(ast={'name': 'foo', 'exp': 'bar'})
    assert repr(named) == "Named(name='foo', exp='bar')"

    named = g.Named(name='foo', exp='bar')
    assert repr(named) == "Named(name='foo', exp='bar')"


def test_calc_repr():
    calc_grammar = r"""
        @@grammar::CALC

        start: expression $

        expression:
            | addition
            | subtraction
            | term

        addition: left:expression op:'+' ~ right:term

        subtraction: left:expression op:'-' ~ right:term

        term:
            | multiplication
            | division
            | factor

        multiplication: left:term op:'*' ~ right:factor

        division: left:term '/' ~ right:factor

        factor:
            | '(' ~ @:expression ')'
            | number

        number: /\d+/
    """

    calc_repr = r"""
        Grammar(
            name='CALC',
            directives={'grammar': 'CALC'},
            rules=[
                Rule(
                    name='start',
                    exp=Sequence(sequence=[Call(name='expression'), EOF(ast='$')]),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=False
                ),
                Rule(
                    name='expression',
                    exp=Choice(
                        options=[
                            Option(exp=Call(name='addition')),
                            Option(exp=Call(name='subtraction')),
                            Option(exp=Call(name='term'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=True,
                    is_memoizable=False
                ),
                Rule(
                    name='addition',
                    exp=Sequence(
                        sequence=[
                            Named(name='left', exp=Call(name='expression')),
                            Named(name='op', exp=Token(token='+')),
                            Cut(ast='~'),
                            Named(name='right', exp=Call(name='term'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=False
                ),
                Rule(
                    name='subtraction',
                    exp=Sequence(
                        sequence=[
                            Named(name='left', exp=Call(name='expression')),
                            Named(name='op', exp=Token(token='-')),
                            Cut(ast='~'),
                            Named(name='right', exp=Call(name='term'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=False
                ),
                Rule(
                    name='term',
                    exp=Choice(
                        options=[
                            Option(exp=Call(name='multiplication')),
                            Option(exp=Call(name='division')),
                            Option(exp=Call(name='factor'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=True,
                    is_memoizable=False
                ),
                Rule(
                    name='multiplication',
                    exp=Sequence(
                        sequence=[
                            Named(name='left', exp=Call(name='term')),
                            Named(name='op', exp=Token(token='*')),
                            Cut(ast='~'),
                            Named(name='right', exp=Call(name='factor'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=False
                ),
                Rule(
                    name='division',
                    exp=Sequence(
                        sequence=[
                            Named(name='left', exp=Call(name='term')),
                            Token(token='/'),
                            Cut(ast='~'),
                            Named(name='right', exp=Call(name='factor'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=False
                ),
                Rule(
                    name='factor',
                    exp=Choice(
                        options=[
                            Option(
                                exp=Sequence(
                                    sequence=[
                                        Token(token='('),
                                        Cut(ast='~'),
                                        Override(name='@', exp=Call(name='expression')),
                                        Token(token=')')
                                    ]
                                )
                            ),
                            Option(exp=Call(name='number'))
                        ]
                    ),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=True
                ),
                Rule(
                    name='number',
                    exp=Pattern(pattern='\\d+'),
                    params=(),
                    kwparams={},
                    decorators=[],
                    is_name=False,
                    is_leftrec=False,
                    is_memoizable=True
                )
            ]
        )
    """

    model = tatsu.compile(calc_grammar, asmodel=True)
    refrepr = trim(calc_repr).rstrip()
    modelrepr = trim(repr(model)).rstrip()
    assert modelrepr == refrepr
