import functools

import pytest

from tatsu import synth
from tatsu.exceptions import FailedParse
from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics
from tatsu.tool import compile, to_python_model


class MyNode:
    def __init__(self, ast):
        pass


def test_builder_semantics():
    grammar = r"""
        start::sum = {number}+ $ ;
        number::int = /\d+/ ;
    """
    text = '5 4 3 2 1'

    semantics = ModelBuilderSemantics()
    model = compile(grammar, 'test')
    ast = model.parse(text, semantics=semantics)
    assert ast == 15

    dotted = functools.partial(str.join, '.')
    dotted.__name__ = 'dotted'  # type: ignore

    grammar = r"""
        start::dotted = {number}+ $ ;
        number = /\d+/ ;
    """

    semantics = ModelBuilderSemantics(types=[dotted])
    model = compile(grammar, 'test')
    ast = model.parse(text, semantics=semantics)
    assert ast == '5.4.3.2.1'


def test_builder_subclassing():
    registry = getattr(synth, '__REGISTRY')

    grammar = """
        @@grammar :: Test
        start::A::B::C = $ ;
    """

    model = compile(grammar, asmodel=True)
    model.parse('', parseinfo=True)

    print(f'{registry=}')
    A = registry['A']
    B = registry['B']
    C = registry['C']

    assert (
        issubclass(A, B) and
        issubclass(A, synth._Synthetic) and
        issubclass(A, Node)
    )
    assert (
        issubclass(B, C) and
        issubclass(B, synth._Synthetic) and
        issubclass(A, Node)
    )
    assert (
        issubclass(C, synth._Synthetic) and
        issubclass(C, Node)
    )


def test_builder_basetype_codegen():
    grammar = """
        @@grammar :: Test
        start::A::B::C = a:() b:() $ ;
        second::D::A = ();
        third = ();
    """

    src = to_python_model(grammar, base_type=MyNode)
    print(src)

    context = {}
    exec(src, context)  # pylint: disable=W0122
    semantics = context['TestModelBuilderSemantics']()

    A = context['A']
    B = context['B']
    C = context['C']
    D = context['D']

    model = compile(grammar, semantics=semantics)
    ast = model.parse('', semantics=semantics)

    assert isinstance(ast, MyNode)
    assert isinstance(ast, (A, B, C))
    assert hasattr(ast, 'a')
    assert hasattr(ast, 'b')

    assert issubclass(D, A | B | C)


def test_optional_attributes():
    grammar = r"""
        foo::Foo = left:identifier [ ':' right:identifier ] $ ;
        identifier = /\w+/ ;
    """

    grammar = compile(grammar)

    a = grammar.parse('foo : bar', semantics=ModelBuilderSemantics())
    assert a.left == 'foo'
    assert a.right == 'bar'

    b = grammar.parse('foo', semantics=ModelBuilderSemantics())
    assert b.left == 'foo'
    assert b.right is None


def test_constant_math():
    grammar = r"""
        start =
            a:A b:B
            @:```{a} / {b}```
            $
        ;

        A = number @:`7` ;
        B = number @:`2` ;
        number::int = /\d+/ ;
    """
    model = compile(grammar)
    result = model.parse('42 84', trace=True)
    assert model
    assert result == 3.5


def test_constant_deep_eval():
    grammar = r"""
        start =
            a:A b:B
            @:```{a} / {b}```
            $
        ;

        A = number @:`7` ;
        B = number @:`0` ;
        number::int = /\d+/ ;
    """
    model = compile(grammar)

    with pytest.raises(FailedParse, match=r'Error evaluating constant.*ZeroDivisionError'):
        # NOTE: only with multiple evaluation passes on constants
        model.parse('42 84', trace=True)
