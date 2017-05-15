# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from tatsu.parser import GrammarGenerator
from tatsu.tool import compile
from tatsu.util import trim, ustr, PY3
from tatsu.codegen import codegen


class ParameterTests(unittest.TestCase):

    def test_keyword_params(self):
        grammar = '''
            start(k1=1, k2=2)
                =
                {'a'} $
                ;
        '''
        g = GrammarGenerator('Keywords')
        model = g.parse(grammar, trace=False)
        code = codegen(model)
        self.assertEqual('#!/usr/bin/env python', code.splitlines()[0])
        pass

    def test_35_only_keyword_params(self):
        grammar = '''
            rule(kwdA=A, kwdB=B)
                =
                'a'
                ;
        '''
        model = compile(grammar, "test")
        self.assertEqual(trim(grammar), ustr(model))

    def test_36_params_and_keyword_params(self):
        grammar = '''
            rule(A, kwdB=B)
                =
                'a'
                ;
        '''
        model = compile(grammar, "test")
        self.assertEqual(trim(grammar), ustr(model))

    def test_36_param_combinations(self):
        def assert_equal(target, value):
            self.assertEqual(target, value)

        class TC36Semantics(object):

            """Check all rule parameters for expected types and values"""

            def rule_positional(self, ast, p1, p2, p3, p4):
                assert_equal("ABC", p1)
                assert_equal(123, p2)
                assert_equal('=', p3)
                assert_equal("+", p4)
                return ast

            def rule_keyword(self, ast, k1, k2, k3, k4):
                assert_equal("ABC", k1)
                assert_equal(123, k2)
                assert_equal('=', k3)
                assert_equal('+', k4)
                return ast

            def rule_all(self, ast, p1, p2, p3, p4, k1, k2, k3, k4):
                assert_equal("DEF", p1)
                assert_equal(456, p2)
                assert_equal('=', p3)
                assert_equal("+", p4)
                assert_equal("HIJ", k1)
                assert_equal(789, k2)
                assert_equal('=', k3)
                assert_equal('+', k4)
                return ast

        grammar = '''
            @@ignorecase::False
            @@nameguard

            start
                = {rule_positional | rule_keywords | rule_all} $ ;
            rule_positional('ABC', 123, '=', '+')
                = 'a' ;
            rule_keywords(k1=ABC, k3='=', k4='+', k2=123)
                = 'b' ;
            rule_all('DEF', 456, '=', '+', k1=HIJ, k3='=', k4='+', k2=789)
                = 'c' ;
        '''

        pretty = '''
            @@ignorecase :: False
            @@nameguard :: True

            start
                =
                {rule_positional | rule_keywords | rule_all} $
                ;


            rule_positional(ABC, 123, '=', '+')
                =
                'a'
                ;


            rule_keywords(k1=ABC, k3='=', k4='+', k2=123)
                =
                'b'
                ;


            rule_all(DEF, 456, '=', '+', k1=HIJ, k3='=', k4='+', k2=789)
                =
                'c'
                ;
        '''

        model = compile(grammar, 'RuleArguments')
        self.assertEqual(trim(pretty), ustr(model))
        model = compile(pretty, 'RuleArguments')

        ast = model.parse("a b c")
        self.assertEqual(['a', 'b', 'c'], ast)
        semantics = TC36Semantics()
        ast = model.parse("a b c", semantics=semantics)
        self.assertEqual(['a', 'b', 'c'], ast)
        codegen(model)

    def test_36_unichars(self):
        grammar = '''
            start = { rule_positional | rule_keywords | rule_all }* $ ;

            rule_positional("ÄÖÜäöüß") = 'a' ;

            rule_keywords(k1='äöüÄÖÜß') = 'b' ;

            rule_all('ßÄÖÜäöü', k1="ßäöüÄÖÜ") = 'c' ;
        '''

        def _trydelete(pymodule):
            import os
            try:
                os.unlink(pymodule + ".py")
            except EnvironmentError:
                pass
            try:
                os.unlink(pymodule + ".pyc")
            except EnvironmentError:
                pass
            try:
                os.unlink(pymodule + ".pyo")
            except EnvironmentError:
                pass

        def assert_equal(target, value):
            self.assertEqual(target, value)

        class UnicharsSemantics(object):
            """Check all rule parameters for expected types and values"""
            def rule_positional(self, ast, p1):
                assert_equal("ÄÖÜäöüß", p1)
                return ast

            def rule_keyword(self, ast, k1):
                assert_equal("äöüÄÖÜß", k1)
                return ast

            def rule_all(self, ast, p1, k1):
                assert_equal("ßÄÖÜäöü", p1)
                assert_equal("ßäöüÄÖÜ", k1)
                return ast

        m = compile(grammar, "UnicodeRuleArguments")
        ast = m.parse("a b c")
        self.assertEqual(['a', 'b', 'c'], ast)

        semantics = UnicharsSemantics()
        ast = m.parse("a b c", semantics=semantics)
        self.assertEqual(['a', 'b', 'c'], ast)

        code = codegen(m)
        import codecs
        with codecs.open("tc36unicharstest.py", "w", "utf-8") as f:
            f.write(code)
        import tc36unicharstest
        tc36unicharstest
        _trydelete("tc36unicharstest")

    def test_numbers_and_unicode(self):
        grammar = '''
            rúle(1, -23, 4.56, 7.89e-11, 0xABCDEF, Añez)
                =
                'a'
                ;
        '''
        rule2 = '''

            rulé::Añez
                =
                '\\xf1'
                ;
        '''
        rule3 = '''

            rúlé::Añez
                =
                'ñ'
                ;
        '''
        if PY3:
            grammar += rule3
        else:
            grammar += rule2

        model = compile(grammar, "test")
        self.assertEqual(trim(grammar), ustr(model))
