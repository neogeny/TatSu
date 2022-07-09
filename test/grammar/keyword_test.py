# -*- coding: utf-8 -*-
import unittest
from ast import parse

from tatsu.exceptions import FailedParse
from tatsu.tool import compile
from tatsu.codegen import codegen


class KeywordTests(unittest.TestCase):

    def test_keywords_in_rule_names(self):
        grammar = '''
            start
                =
                whitespace
                ;

            whitespace
                =
                    {'x'}+
                ;
        '''
        m = compile(grammar, 'Keywords')
        m.parse('x')

    def test_python_keywords_in_rule_names(self):
        # This is a regression test for
        # https://bitbucket.org/neogeny/tatsu/issues/59
        # (semantic actions not called for rules with the same name as a python
        # keyword).
        grammar = '''
            not = 'x' ;
        '''
        m = compile(grammar, 'Keywords')

        class Semantics:
            def __init__(self):
                self.called = False

            def not_(self, ast):
                self.called = True

        semantics = Semantics()
        m.parse('x', semantics=semantics)
        assert semantics.called

    def test_define_keywords(self):
        grammar = '''
            @@keyword :: B C
            @@keyword :: 'A'

            start = ('a' 'b').{'x'}+ ;
        '''
        model = compile(grammar, "test")
        c = codegen(model)
        parse(c)

        grammar2 = str(model)
        model2 = compile(grammar2, "test")
        c2 = codegen(model2)
        parse(c2)

        self.assertEqual(grammar2, str(model2))

    def test_check_keywords(self):
        grammar = r'''
            @@keyword :: A

            start = {id}+ $ ;

            @name
            id = /\w+/ ;
        '''
        model = compile(grammar, 'test')
        c = codegen(model)
        parse(c)

        ast = model.parse('hello world')
        self.assertEqual(['hello', 'world'], ast)

        try:
            ast = model.parse("hello A world")
            self.assertEqual(['hello', 'A', 'world'], ast)
            self.fail('accepted keyword as name')
        except FailedParse as e:
            self.assertTrue('"A" is a reserved word' in str(e))

    def test_check_unicode_name(self):
        grammar = r'''
            @@keyword :: A

            start = {id}+ $ ;

            @name
            id = /\w+/ ;
        '''
        model = compile(grammar, 'test')
        model.parse("hello Øresund")

    def test_sparse_keywords(self):
        grammar = r'''
            @@keyword :: A

            @@ignorecase :: False

            start = {id}+ $ ;

            @@keyword :: B

            @name
            id = /\w+/ ;
        '''
        model = compile(grammar, 'test', trace=False, colorize=True)
        c = codegen(model)
        parse(c)

        ast = model.parse('hello world')
        self.assertEqual(['hello', 'world'], ast)

        for k in ('A', 'B'):
            try:
                ast = model.parse("hello %s world" % k)
                self.assertEqual(['hello', k, 'world'], ast)
                self.fail('accepted keyword "%s" as name' % k)
            except FailedParse as e:
                self.assertTrue('"%s" is a reserved word' % k in str(e))

    def test_ignorecase_keywords(self):
        grammar = '''
            @@ignorecase :: True
            @@keyword :: if

            start = rule ;

            @name
            rule = @:word if_exp $ ;

            if_exp = 'if' digit ;

            word = /\w+/ ;
            digit = /\d/ ;
        '''

        model = compile(grammar, 'test')

        model.parse('nonIF if 1', trace=False)

        with self.assertRaises(FailedParse):
            model.parse('i rf if 1', trace=False)

        with self.assertRaises(FailedParse):
            model.parse('IF if 1', trace=False)
