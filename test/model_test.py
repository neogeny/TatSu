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
