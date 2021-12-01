# -*- coding: utf-8 -*-
import unittest
import pickle

from tatsu.semantics import ModelBuilderSemantics
from tatsu.tool import compile


class PickleTest(unittest.TestCase):

    def test_synth_model(self):
        grammar = '''
            start::ASeq
                =
                aseq
                $
                ;

            aseq
                =
                {'a'}+
                ;
        '''

        m = compile(grammar, 'ASeq')
        model = m.parse('a a a', semantics=ModelBuilderSemantics())
        self.assertEqual('ASeq', type(model).__name__)

        p = pickle.dumps(model)
        new_model = pickle.loads(p)
        self.assertEqual('ASeq', type(new_model).__name__)

        self.assertEqual(model.ast, new_model.ast)

    def test_nested_class_synth_model(self):
        grammar = '''
            start::ASeq
                =
                seqs:aseq
                $
                ;

            aseq::Seq
                =
                values:{'a'}+
                ;
        '''

        m = compile(grammar, 'ASeq')
        model = m.parse('a a a', semantics=ModelBuilderSemantics())
        self.assertEqual('ASeq', type(model).__name__)

        p = pickle.dumps(model)
        new_model = pickle.loads(p)
        self.assertEqual('ASeq', type(new_model).__name__)

        # NOTE: Since we are unpickling an object which contains nested objects, we can't do
        # self.assertEqual(model.ast, new_model.ast) as the memory locations will be different.
        # So either (1) we recursively walk the objects and compare fields or (2) we convert it into a
        # str()/repr() and compare that. Do the latter as it is easier.
        self.assertEqual(str(model.ast), str(new_model.ast))
