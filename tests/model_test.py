# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import json  # noqa: F401
import pprint  # noqa: F401
from typing import Any

import pytest

import tatsu
from tatsu import grammars as g
from tatsu.ast import AST
from tatsu.objectmodel import Node
from tatsu.util import hasha, typename
from tatsu.util.string import trim


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
    assert isinstance(model, AST)
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

    with pytest.raises(TypeError, match=r"required.*'name'"):
        g.Named()

    named = g.Named(name='foo')
    assert repr(named) == f"Named(name='foo', exp={g.NULL.__name__}())"

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

        addition[Add]: left:expression op:'+' ~ right:term

        subtraction[Subtract]: left:expression op:'-' ~ right:term

        term:
            | multiplication
            | division
            | factor

        multiplication[Multiply]: left:term op:'*' ~ right:factor

        division[Divide]: left:term '/' ~ right:factor

        factor:
            | '(' ~ @:expression ')'
            | number

        number[int]: /\d+/
    """

    calc_repr = r"""
        Grammar(
          name='CALC',
          directives={'grammar': 'CALC'},
          rules=(
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
              params=['Add'],
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
              params=['Subtract'],
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
              params=['Multiply'],
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
              params=['Divide'],
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
                        Override(exp=Call(name='expression')),
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
              params=['int'],
              kwparams={},
              decorators=[],
              is_name=False,
              is_leftrec=False,
              is_memoizable=True
            )
          )
        )
    """

    model = tatsu.compile(calc_grammar, asmodel=True)
    modelrepr = trim(repr(model)).rstrip()

    # HACK FIXME
    # from pathlib import Path
    # Path('calcmodel.py').write_text(modelrepr)

    refrepr = trim(calc_repr).rstrip()
    assert modelrepr == refrepr
    # assert hasha(modelrepr) == hasha(refrepr)
    emodel = eval(modelrepr, vars(g), {})  # type: ignore # noqa: S307
    assert isinstance(emodel, g.Grammar)
    assert isinstance(emodel.rules[0], g.Rule)
    assert emodel.name == 'CALC'
    assert emodel.rules[0].name == 'start'
    assert emodel.rules[-1].name == 'number'
    assert isinstance(emodel.rules[-1].exp, g.Pattern)
    assert hasha(repr(emodel).strip()) == hasha(refrepr)

    exp = emodel.parse('3 * 2 + 1', asmodel=True)
    assert typename(exp) == 'Add'
    assert typename(exp.left) == 'Multiply'  # type: ignore
    assert typename(exp.right) == 'int'  # type: ignore

    addmodel = emodel.rulemap['addition']
    assert isinstance(addmodel, g.Model)
    assert addmodel.grammar is emodel

    addresult = addmodel.parse('2 + 2', asmodel=False)
    assert addresult == {'left': '2', 'op': '+', 'right': '2'}

    exp = emodel.parse('3', start='number', asmodel=True)
    assert isinstance(exp, int)
    assert exp == 3

    exp = emodel.parse('3', asmodel=False)
    assert isinstance(exp, str)
    assert exp == '3'

    assert pprint.pformat(emodel).rstrip() == refrepr

    # test rule access by name
    assert isinstance(model.rule.start, g.Rule)
    assert isinstance(model.rule.addition, g.Rule)
    assert isinstance(model.rule.multiplication, g.Rule)
