import pytest

from tatsu import synth
from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics
from tatsu.tool import compile


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

    import functools

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
    model.parse('')

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

    from tatsu.tool import to_python_model

    src = to_python_model(grammar, base_type=MyNode)
    print(src)

    globals = {}
    exec(src, globals)  # pylint: disable=W0122
    semantics = globals['TestModelBuilderSemantics']()

    A = globals['A']
    B = globals['B']
    C = globals['C']
    D = globals['D']

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


@pytest.mark.skip(reason='Not finished yer')
def test_constant_failure():
    grammar = r"""
        start =
            a:A b:B
            c:```{a} / {b}```
            $
        ;

        A = number @:`7` ;
        B = number @:`0` ;
        number::int = /\d+/ ;
    """
    try:
        model = compile(grammar)
        result = model.parse('42 84', trace=True)
    except Exception as e:
        print(e)
        raise
    assert model
    assert result == []
    pytest.fail('should not have reached here')
