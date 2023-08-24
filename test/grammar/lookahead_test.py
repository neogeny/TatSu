# -*- coding: utf-8 -*-
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
        self.assertEqual(('x', ('a', 'b')), ast)

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
        self.assertEqual(('x', ('a', 'b')), ast)
