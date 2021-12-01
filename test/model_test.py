# -*- coding: utf-8 -*-
from __future__ import generator_stop

from tatsu.objectmodel import Node


def test_node_kwargs():
    class Atom(Node):
        symbol: str = None
        arguments: str = None

    atom = Atom(symbol='foo', ast={})
    assert atom.symbol == 'foo'

    atom = Atom(symbol='foo')
    assert atom.symbol == 'foo'
