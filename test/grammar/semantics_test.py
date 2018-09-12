# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from tatsu.tool import compile
from tatsu.semantics import ModelBuilderSemantics


class MyNode(object):
    def __init__(self, ast):
        pass


class SemanticsTests(unittest.TestCase):

    def test_builder_semantics(self):
        grammar = '''
            start::sum = {number}+ $ ;
            number::int = /\d+/ ;
        '''
        text = '5 4 3 2 1'

        semantics = ModelBuilderSemantics()
        model = compile(grammar, 'test')
        ast = model.parse(text, semantics=semantics)
        self.assertEqual(15, ast)

        import functools
        dotted = functools.partial(type('').join, '.')
        dotted.__name__ = 'dotted'

        grammar = '''
            start::dotted = {number}+ $ ;
            number = /\d+/ ;
        '''

        semantics = ModelBuilderSemantics(types=[dotted])
        model = compile(grammar, 'test')
        ast = model.parse(text, semantics=semantics)
        self.assertEqual('5.4.3.2.1', ast)

    def test_builder_subclassing(self):
        from tatsu import synth
        from tatsu.model import Node

        registry = getattr(synth, "__REGISTRY")

        grammar = '''
            @@grammar :: Test
            start::A::B::C = $ ;
        '''

        model = compile(grammar, asmodel=True)
        model.parse("")

        A = registry["A"]
        B = registry["B"]
        C = registry["C"]

        self.assertTrue(issubclass(A, B) and issubclass(A, synth._Synthetic) and issubclass(A, Node))
        self.assertTrue(issubclass(B, C) and issubclass(B, synth._Synthetic) and issubclass(A, Node))
        self.assertTrue(issubclass(C, synth._Synthetic) and issubclass(C, Node))

    def test_builder_basetype_codegen(self):
        grammar = '''
            @@grammar :: Test
            start::MyNode = $ ;
        '''

        from tatsu.tool import to_python_model
        src = to_python_model(grammar, base_type=MyNode)
        globals = {}
        exec(src, globals)
        semantics = globals["TestModelBuilderSemantics"]()

        model = compile(grammar, semantics=semantics)

        ast = model.parse("", semantics=semantics)
        self.assertIsInstance(ast, MyNode)
