from __future__ import generator_stop

import unittest
from ast import parse

from tatsu.exceptions import FailedParse
from tatsu.tool import compile
from tatsu.codegen import codegen
from tatsu.util import trim


class JoinTests(unittest.TestCase):

    def test_positive_join(self):
        grammar = '''
            start = ','%{'x' 'y'}+ ;
        '''

        grammar2 = '''
            start = (','%{'x'}+|{}) ;
        '''

        grammar3 = '''
            start = [','%{'x'}+] ;
        '''

        model = compile(grammar, "test")
        codegen(model)
        ast = model.parse("x y, x y", nameguard=False)
        self.assertEqual([['x', 'y'], ',', ['x', 'y']], ast)
        ast = model.parse("x y x y", nameguard=False)
        self.assertEqual([['x', 'y']], ast)
        try:
            ast = model.parse("y x", nameguard=False)
            self.fail('closure not positive')
        except FailedParse:
            pass

        model = compile(grammar2, "test")
        ast = model.parse("y x", nameguard=False)
        self.assertEqual([], ast)
        ast = model.parse("x", nameguard=False)
        self.assertEqual(['x'], ast)
        ast = model.parse("x,x", nameguard=False)
        self.assertEqual(['x', ',', 'x'], ast)

        model = compile(grammar3, "test")
        ast = model.parse("y x", nameguard=False)
        self.assertEqual(None, ast)

    def test_normal_join(self):
        grammar = '''
            start = ','%{'x' 'y'} 'z' ;
        '''

        model = compile(grammar, "test")
        codegen(model)

        ast = model.parse("x y, x y z", nameguard=False)
        self.assertEqual(([['x', 'y'], ',', ['x', 'y']], 'z'), ast)

        ast = model.parse("x y z", nameguard=False)
        self.assertEqual(([['x', 'y']], 'z'), ast)

        ast = model.parse("z", nameguard=False)
        self.assertEqual(([], 'z'), ast)

    def test_group_join(self):
        grammar = '''
            start = ('a' 'b')%{'x'}+ ;
        '''
        model = compile(grammar, "test")
        c = codegen(model)
        parse(c)

        ast = model.parse("x a b x", nameguard=False)
        self.assertEqual(['x', ['a', 'b'], 'x'], ast)

    def test_positive_gather(self):
        grammar = '''
            start = ','.{'x' 'y'}+ ;
        '''

        grammar2 = '''
            start = (','.{'x'}+|{}) ;
        '''

        grammar3 = '''
            start = [','.{'x'}+] ;
        '''

        model = compile(grammar, "test")
        codegen(model)
        ast = model.parse("x y, x y", nameguard=False)
        self.assertEqual([['x', 'y'], ['x', 'y']], ast)
        ast = model.parse("x y x y", nameguard=False)
        self.assertEqual([['x', 'y']], ast)
        try:
            ast = model.parse("y x", nameguard=False)
            self.fail('closure not positive')
        except FailedParse:
            pass

        model = compile(grammar2, "test")
        ast = model.parse("y x", nameguard=False)
        self.assertEqual([], ast)
        ast = model.parse("x", nameguard=False)
        self.assertEqual(['x'], ast)
        ast = model.parse("x,x", nameguard=False)
        self.assertEqual(['x', 'x'], ast)

        model = compile(grammar3, "test")
        ast = model.parse("y x", nameguard=False)
        self.assertEqual(None, ast)

    def test_normal_gather(self):
        grammar = '''
            start = ','.{'x' 'y'} 'z' ;
        '''

        model = compile(grammar, "test")
        codegen(model)

        ast = model.parse("x y, x y z", nameguard=False)
        self.assertEqual(([['x', 'y'], ['x', 'y']], 'z'), ast)

        ast = model.parse("x y z", nameguard=False)
        self.assertEqual(([['x', 'y']], 'z'), ast)

        ast = model.parse("z", nameguard=False)
        self.assertEqual(([], 'z'), ast)

    def test_group_gather(self):
        grammar = '''
            start = ('a' 'b').{'x'}+ ;
        '''
        model = compile(grammar, "test")
        c = codegen(model)
        parse(c)

        ast = model.parse("x a b x", nameguard=False)
        self.assertEqual(['x', 'x'], ast)

    def test_left_join(self):
        grammar = r'''
            start
                =
                (op)<{number}+ $
                ;


            op
                =
                '+' | '-'
                ;


            number
                =
                /\d+/
                ;
        '''
        text = '1 + 2 - 3 + 4'

        model = compile(grammar, "test")
        self.assertEqual(trim(grammar).strip(), str(model).strip())
        codegen(model)

        ast = model.parse(text)
        self.assertEqual(
            (
                '+',
                (
                    '-',
                    (
                        '+',
                        '1',
                        '2'
                    ),
                    '3'
                ),
                '4'
            ),
            ast
        )

    def test_right_join(self):
        grammar = r'''
            start
                =
                (op)>{number}+ $
                ;


            op
                =
                '+' | '-'
                ;


            number
                =
                /\d+/
                ;
        '''
        text = '1 + 2 - 3 + 4'

        model = compile(grammar, "test")
        self.assertEqual(trim(grammar).strip(), str(model).strip())
        codegen(model)

        ast = model.parse(text)
        self.assertEqual(
            (
                '+',
                '1',
                (
                    '-',
                    '2',
                    (
                        '+',
                        '3',
                        '4'
                    )
                )
            ),
            ast
        )
