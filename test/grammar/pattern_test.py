# -*- coding: utf-8 -*-
import unittest

from tatsu.util import trim
from tatsu.tool import compile
from tatsu.exceptions import FailedParse
from tatsu.codegen import codegen


class PatternTests(unittest.TestCase):

    def test_patterns_with_newlines(self):
        grammar = '''
            @@whitespace :: /[ \t]/
            start
                =
                blanklines $
                ;

            blanklines
                =
                blankline [blanklines]
                ;

            blankline
                =
                /^[^\\n]*\\n$/
                ;
        '''

        model = compile(grammar, "test")
        ast = model.parse('\n\n')
        self.assertEqual(('\n', '\n'), ast)

    def test_pattern_concatenation(self):
        grammar = '''
            start
                =
                {letters_digits}+
                ;


            letters_digits
                =
                ?"[a-z]+"
                + ?'[0-9]+'
                ;
        '''
        pretty = '''
            start
                =
                {letters_digits}+
                ;


            letters_digits
                =
                /[a-z]+/
                + /[0-9]+/
                ;
        '''
        model = compile(grammar=grammar)
        ast = model.parse('abc123 def456')
        self.assertEqual(['abc123', 'def456'], ast)
        print(model.pretty())
        self.assertEqual(trim(pretty), model.pretty())

    def test_ignorecase_not_for_pattern(self):
        grammar = '''
            @@ignorecase
            start
                =
                {word} $
                ;

            word
                =
                /[a-z]+/
                ;
        '''

        model = compile(grammar=grammar)
        try:
            model.parse('ABcD xYZ')
            self.fail('@@ignorecase should not apply to patterns')
        except FailedParse:
            pass

    def test_ignorecase_pattern(self):
        grammar = '''
            start
                =
                {word} $
                ;

            word
                =
                /(?i)[a-z]+/
                ;
        '''

        model = compile(grammar=grammar)
        ast = model.parse('ABcD xYZ')
        self.assertEqual(['ABcD', 'xYZ'], ast)

    def test_multiline_pattern(self):
        grammar = r'''
            start =
            /(?x)
            foo
            bar
            / $ ;
        '''
        model = compile(grammar=trim(grammar))
        print(codegen(model.rules[0].exp.sequence[0]))
        self.assertEqual(
            codegen(model.rules[0].exp.sequence[0]),
            repr("self._pattern('(?x)\nfoo\nbar\n')").strip('"\'')
        )

        grammar = r'''
            start =
            /(?x)foo\nbar
            blort/ $ ;
        '''
        model = compile(grammar=trim(grammar))
        print(codegen(model.rules[0].exp.sequence[0]))
        self.assertEqual(
            trim(codegen(model.rules[0].exp.sequence[0])),
            repr("self._pattern('(?x)foo\\nbar\nblort')").strip(r'"\.')
        )
