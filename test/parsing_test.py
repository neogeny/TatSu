# -*- coding: utf-8 -*-
import unittest
import tempfile

import tatsu
from tatsu.util import trim, eval_escapes
from tatsu.grammars import EBNFBuffer


class MockIncludeBuffer(EBNFBuffer):
    def get_include(self, source, filename):
        return '\nINCLUDED "%s"\n' % filename, filename


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

    def test_real_include(self):
        _, include_a = tempfile.mkstemp(suffix='.ebnf', prefix='include_')
        _, include_b = tempfile.mkstemp(suffix='.ebnf', prefix='include_')

        grammar = '''\
            #include :: "{include_a}"
            #include :: "{include_b}"

            start = a b;'''

        with open(include_a, 'w') as fh:
            fh.write('a = \'inclusion\';')
        with open(include_b, 'w') as fh:
            fh.write('b = \'works\';')

        model = tatsu.compile(grammar=grammar.format(include_a=include_a, include_b=include_b))
        self.assertIsNotNone(model)

    def test_escape_sequences(self):
        self.assertEqual('\n', eval_escapes(r'\n'))
        self.assertEqual('this \xeds a test', eval_escapes(r'this \xeds a test'))
        self.assertEqual('this ís a test', eval_escapes(r'this \xeds a test'))
        self.assertEqual('\nañez', eval_escapes(r'\na\xf1ez'))
        self.assertEqual('\nañez', eval_escapes(r'\nañez'))

    def test_start(self):
        grammar = '''
            @@grammar :: Test

            true = "test" @:`True` $;
            false = "test" @:`False` $;

        '''
        model = tatsu.compile(grammar=grammar)
        self.assertEqual('Test', model.directives.get('grammar'))
        self.assertEqual('Test', model.name)

        # By default, parsing starts from the first rule in the grammar.
        ast = model.parse("test")
        self.assertEqual(ast, True)

        # The start rule can be passed explicitly.
        ast = model.parse("test", start='true')
        self.assertEqual(ast, True)
        # Backward compatibility argument name.
        ast = model.parse("test", rule_name='true')
        self.assertEqual(ast, True)

        # The default rule can be overwritten.
        ast = tatsu.parse(grammar, "test", start='false')
        self.assertEqual(ast, False)
        # Backward compatibility argument name.
        ast = tatsu.parse(grammar, "test", rule_name='false')
        self.assertEqual(ast, False)

    def test_rule_capitalization(self):
        grammar = '''
            start = ['test' {rulename}] ;
            {rulename} = /[a-zA-Z0-9]+/ ;
        '''
        test_string = 'test 12'
        lowercase_rule_names = ['nocaps', 'camelCase', 'tEST']
        uppercase_rule_names = ['Capitalized', 'CamelCase', 'TEST']
        ref_lowercase_result = tatsu.parse(grammar.format(rulename='reflowercase'), test_string)
        ref_uppercase_result = tatsu.parse(grammar.format(rulename='Refuppercase'), test_string)
        for rulename in lowercase_rule_names:
            result = tatsu.parse(grammar.format(rulename=rulename), test_string)
            self.assertEqual(result, ref_lowercase_result)
        for rulename in uppercase_rule_names:
            result = tatsu.parse(grammar.format(rulename=rulename), test_string)
            self.assertEqual(result, ref_uppercase_result)

    def test_startrule_issue62(self):
        grammar = '''
            @@grammar::TEST

            file_input = expr $ ;
            expr = number '+' number ;
            number = /[0-9]/ ;
        '''
        model = tatsu.compile(grammar=grammar)
        model.parse('4 + 5')


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ParsingTests)


def main():
    unittest.TextTestRunner(verbosity=2).run(suite())


if __name__ == '__main__':
    main()
