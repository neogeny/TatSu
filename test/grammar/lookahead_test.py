# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from tatsu.tool import compile


class LookaheadTests(unittest.TestCase):
    def test_skip_to(self, trace=False):
        grammar = '''
            start = 'x' ab $ ;

            ab
                =
                | 'a' 'b'
                | ->'a' 'b'
                ;
        '''
        m = compile(grammar, trace=trace)
        ast = m.parse('x xx yyy a b')
        self.assertEqual(['x', ['a', 'b']], ast)

        grammar = '''
            start = 'x' ab $ ;

            ab
                =
                | 'a' 'b'
                | ->&'a' 'a' 'b'
                ;
        '''
        m = compile(grammar, trace=trace)
        ast = m.parse('x xx yyy a b')
        self.assertEqual(['x', ['a', 'b']], ast)
