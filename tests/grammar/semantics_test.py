# Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
# SPDX-License-Identifier: BSD-4-Clause
from __future__ import annotations

import sys

import pytest

from tatsu import synth
from tatsu.builder import BuilderConfig, ModelBuilder, TypeResolutionError
from tatsu.exceptions import FailedParse, FailedToken
from tatsu.objectmodel import Node
from tatsu.tool import compile, parse


class MyNode:
    def __init__(self, ast):
        pass


class BType:
    pass


class AType(BType):
    pass


def test_semantics_not_class():
    grammar = r"""
        start::sum = {number}+ $ ;
        number::int = /\d+/ ;
    """
    text = '5 4 3 2 1'
    bad_semantics = ModelBuilder  # NOTE: the class
    semantics = ModelBuilder()  # NOTE: the class

    with pytest.raises(TypeError, match=r'semantics must be an object instance or None.*'):
        compile(grammar, semantics=bad_semantics)
        compile(grammar, semantics=bad_semantics)

    model = compile(grammar, 'test')
    with pytest.raises(TypeError, match=r'semantics must be an object instance or None.*'):
        model.parse(text, semantics=bad_semantics)

    ast = model.parse(text, semantics=semantics)
    assert ast == 15


def test_builder_semantics():
    grammar = r"""
        start::sum = {number}+ $ ;
        number::int = /\d+/ ;
    """
    text = '5 4 3 2 1'

    semantics = ModelBuilder()
    model = compile(grammar, 'test')
    ast = model.parse(text, semantics=semantics)
    assert ast == 15

    import functools

    dotted = functools.partial(str.join, '.')
    # WARNING: this defeats all TatSu knows about functions and types
    #  dotted.__name__ = 'dotted'

    grammar = r"""
        start::dotted = {number}+ $ ;
        number = /\d+/ ;
    """

    semantics = ModelBuilder(constructors=[dotted])
    model = compile(grammar, 'test')
    with pytest.raises(TypeResolutionError, match=r"Could not find constructor for type 'dotted'"):
        ast = model.parse(text, semantics=semantics)
        assert ast == '5.4.3.2.1'


def test_builder_subclassing():
    registry = getattr(synth, '__registry')

    grammar = """
        @@grammar :: Test
        start::A::B::C = $ ;
    """

    model = compile(grammar, asmodel=True)
    model.parse('')

    print(f'{registry=}')
    A = registry['A']
    B = registry['B']
    C = registry['C']

    assert (
        issubclass(A, B) and
        issubclass(A, synth.SynthNode) and
        issubclass(A, Node)
    )
    assert (
        issubclass(B, C) and
        issubclass(B, synth.SynthNode) and
        issubclass(A, Node)
    )
    assert (
        issubclass(C, synth.SynthNode) and
        issubclass(C, Node)
    )


def test_builder_basetype_codegen():
    grammar = """
        @@grammar :: Test
        start::A::B::C = a:() b:() $ ;
        second::D::A = ();
        third = ();
    """

    from tatsu.tool import to_python_model

    src = to_python_model(grammar, basetype=MyNode)
    # print(src[:1000])

    globals = {}
    exec(src, globals)  # pylint: disable=W0122
    semantics = globals['TestModelBuilder']()

    A = globals['A']
    B = globals['B']
    C = globals['C']
    D = globals['D']

    model = compile(grammar, semantics=semantics)
    ast = model.parse('', semantics=semantics)
    # print(f'AST({type(ast)}=', ast)

    assert isinstance(ast, MyNode), A.__mro__
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

    a = grammar.parse('foo : bar', semantics=ModelBuilder())
    assert a.left == 'foo'
    assert a.right == 'bar'

    b = grammar.parse('foo', semantics=ModelBuilder())
    assert b.left == 'foo'
    assert b.right is None


def test_constant_math():
    grammar = r"""
        start = a:`7` b:`2` @:```{a} / {b}``` $ ;
    """
    result = parse(grammar, '', trace=True)
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


def test_builder_types():
    grammar = """
        @@grammar :: Test
        start::AType::BType = $ ;
    """

    builderconfig = BuilderConfig(basetype=BType, constructors=[AType, BType])
    ast = parse(grammar, '', builderconfig=builderconfig)
    assert type(ast) is AType
    assert isinstance(ast, BType)
    assert not isinstance(ast, synth.SynthNode)


def test_builder_nodedefs():
    grammar = """
        @@grammar :: Test
        start::AType::BType = $ ;
    """

    thismodule = sys.modules[__name__]
    builderconfig = BuilderConfig(typedefs=[thismodule], synthok=False)
    ast = parse(grammar, '', builderconfig=builderconfig)
    assert type(ast) is AType
    assert isinstance(ast, BType)
    assert not isinstance(ast, synth.SynthNode)


def test_ast_per_option():
    grammar = """
        start = options $ ;

        options =
            | a:'a' [b:'b']
            | c:'c' [d:'d']
            ;
    """

    # NOTE:
    #   Prove each option in a choide has its own version of the AST

    ast = parse(grammar, 'a b')
    assert ast == {'a': 'a', 'b': 'b'}
    assert 'c' not in ast
    assert 'd' not in ast

    ast = parse(grammar, 'c d')
    assert ast == {'c': 'c', 'd': 'd'}
    assert 'a' not in ast
    assert 'b' not in ast

    ast = parse(grammar, 'a')
    assert ast == {'a': 'a', 'b': None}
    assert 'b' in ast
    assert 'c' not in ast
    assert 'd' not in ast

    ast = parse(grammar, 'c')
    assert ast == {'c': 'c', 'd': None}
    assert 'd' in ast
    assert 'a' not in ast
    assert 'b' not in ast


def test_ast_names_accumulate():
    grammar = """
        start = options $ ;

        options =
            | a:'a' ([b:'b'] {x:'x'})
            | c:'c' ([d:'d'] y:{'y'})
            ;
    """

    # NOTE:
    #   Prove named elements accumulat
    ast = parse(grammar, 'a')
    assert ast == {'a': 'a', 'b': None}

    ast = parse(grammar, 'a x')
    assert ast == {'a': 'a', 'b': None, 'x': 'x'}

    ast = parse(grammar, 'a x x')
    assert ast == {'a': 'a', 'b': None, 'x': ['x', 'x']}

    # NOTE:
    #   Prove naming closures always closure
    ast = parse(grammar, 'c')
    assert ast == {'c': 'c', 'd': None, 'y': []}

    ast = parse(grammar, 'c y')
    assert ast == {'c': 'c', 'd': None, 'y': ['y']}

    ast = parse(grammar, 'c y y')
    assert ast == {'c': 'c', 'd': None, 'y': ['y', 'y']}


def test_cut_scope():
    grammar = """
        start = failcut | failchoice | succeed $ ;

        failcut = 'a' ~ 'y' ;

        failchoice =
            | 'a' ~ 'b'
            | 'a' 'c' 'd'
            ;

        succeed = 'a' 'x' ;
    """

    ast = parse(grammar, 'a x')
    assert ast == ('a', 'x')

    ast = parse(grammar, 'a b')
    assert ast == ('a', 'b')

    ast = parse(grammar, 'a y')
    assert ast == ('a', 'y')

    with pytest.raises(FailedToken, match=r"expecting 'y'"):
        ast = parse(grammar, 'a c d')
        assert ast == ('a', 'c', 'd')
