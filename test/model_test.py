import json  # noqa, pylint: disable=unused-import
import tatsu
from tatsu.objectmodel import Node


def test_node_kwargs():
    class Atom(Node):
        def __init__(self, arguments=None, symbol=None, **_kwargs_):
            self.symbol = None
            super().__init__(
                arguments=arguments,
                symbol=symbol,
                **_kwargs_
            )

    atom = Atom(symbol='foo')
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

    parser = tatsu.compile(grammar, asmodel=True)
    assert parser
    model = parser.parse('3 + 5 * ( 10 - 20 )', asmodel=True)
    assert model
    assert model['add']
    assert model['add'].children()
    assert type(model['add'].children()[0]).__name__ == 'Multiply'
