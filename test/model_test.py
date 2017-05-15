# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from tatsu.objectmodel import Node


class ModelTests(unittest.TestCase):
    def test_node_kwargs(self):
        class Atom(Node):
            def __init__(self, arguments=None, symbol=None, **_kwargs_):
                super(Atom, self).__init__(
                    arguments=arguments,
                    symbol=symbol,
                    **_kwargs_
                )

        atom = Atom(symbol='foo', ast={})
        self.assertIsNotNone(atom.symbol)
        self.assertEqual(atom.symbol, 'foo')

        atom = Atom(symbol='foo')
        self.assertIsNotNone(atom.symbol)
        self.assertEqual(atom.symbol, 'foo')
