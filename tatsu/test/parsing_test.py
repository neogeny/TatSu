# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

import tatsu
from tatsu.util import trim, eval_escapes
from tatsu.grammars import EBNFBuffer


class MockIncludeBuffer(EBNFBuffer):
    def get_include(self, source, name):
        return '\nINCLUDED "%s"\n' % name, name


class ParsingTests(unittest.TestCase):
    def test_include(self):
        text = '''\
            first
                #include :: "something"
            last\
        '''
        buf = MockIncludeBuffer(trim(text))
        self.assertEqual('first\n\nINCLUDED "something"\nlast', buf.text)

    def test_multiple_include(self):
        text = '''\
            first
                #include :: "something"
                #include :: "anotherthing"
            last\
        '''
        buf = MockIncludeBuffer(trim(text))
        self.assertEqual('first\n\nINCLUDED "something"\n\nINCLUDED "anotherthing"\nlast', buf.text)

    def test_escape_sequences(self):
        self.assertEqual(u'\n', eval_escapes(r'\n'))
        self.assertEqual(u'this \xeds a test', eval_escapes(r'this \xeds a test'))
        self.assertEqual(u'this ís a test', eval_escapes(r'this \xeds a test'))
        self.assertEqual(u'\nañez', eval_escapes(r'\na\xf1ez'))
        self.assertEqual(u'\nañez', eval_escapes(r'\nañez'))

    def test_rule_name(self):
        grammar = '''
            @@grammar :: Test

            start = test $;
            test = "test";
        '''
        model = tatsu.compile(grammar=grammar)
        self.assertEqual('Test', model.directives.get('grammar'))
        self.assertEqual('Test', model.name)

        ast = model.parse("test")
        self.assertEqual(ast, "test")

        ast = tatsu.parse(grammar, "test", rule_name='start')
        self.assertEqual(ast, "test")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ParsingTests)


def main():
    unittest.TextTestRunner(verbosity=2).run(suite())


if __name__ == '__main__':
    main()
