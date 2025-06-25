import contextlib
import pathlib
import sys
import tempfile
import unittest

from tatsu.ngcodegen import codegen
from tatsu.parser import GrammarGenerator
from tatsu.tool import compile
from tatsu.util import trim


class ParameterTests(unittest.TestCase):
    def test_keyword_params(self):
        grammar = """
            start(k1=1, k2=2)
                =
                {'a'} $
                ;
        """
        g = GrammarGenerator('Keywords')
        model = g.parse(grammar)
        code = codegen(model)
        self.assertEqual('#!/usr/bin/env python3', code.splitlines()[0])

    def test_35_only_keyword_params(self):
        grammar = """
            rule(kwdA=A, kwdB=B)
                =
                'a'
                ;
        """
        model = compile(grammar, 'test')
        self.assertEqual(trim(grammar), str(model))

    def test_36_params_and_keyword_params(self):
        grammar = """
            rule(A, kwdB=B)
                =
                'a'
                ;
        """
        model = compile(grammar, 'test')
        self.assertEqual(trim(grammar), str(model))

    def test_36_param_combinations(self):
        def assert_equal(target, value):
            self.assertEqual(target, value)

        class TC36Semantics:

            """Check all rule parameters for expected types and values"""

            def rule_positional(self, ast, p1, p2, p3, p4):
                assert_equal('ABC', p1)
                assert_equal(123, p2)
                assert_equal('=', p3)
                assert_equal('+', p4)
                return ast

            def rule_keyword(self, ast, k1, k2, k3, k4):
                assert_equal('ABC', k1)
                assert_equal(123, k2)
                assert_equal('=', k3)
                assert_equal('+', k4)
                return ast

            def rule_all(self, ast, p1, p2, p3, p4, k1, k2, k3, k4):
                assert_equal('DEF', p1)
                assert_equal(456, p2)
                assert_equal('=', p3)
                assert_equal('+', p4)
                assert_equal('HIJ', k1)
                assert_equal(789, k2)
                assert_equal('=', k3)
                assert_equal('+', k4)
                return ast

        grammar = """
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
        """

        pretty = """
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
        """

        model = compile(grammar, 'RuleArguments')
        self.assertEqual(trim(pretty), str(model))
        model = compile(pretty, 'RuleArguments')

        ast = model.parse('a b c')
        self.assertEqual(['a', 'b', 'c'], ast)
        semantics = TC36Semantics()
        ast = model.parse('a b c', semantics=semantics)
        self.assertEqual(['a', 'b', 'c'], ast)
        codegen(model)

    def test_36_unichars(self):
        grammar = """
            start = { rule_positional | rule_keywords | rule_all }* $ ;

            rule_positional("ÄÖÜäöüß") = 'a' ;

            rule_keywords(k1='äöüÄÖÜß') = 'b' ;

            rule_all('ßÄÖÜäöü', k1="ßäöüÄÖÜ") = 'c' ;
        """

        def _trydelete(pypath, pymodule):
            module_with_path = pypath / pymodule

            with contextlib.suppress(OSError):
                module_with_path.with_suffix('.py').unlink()
            with contextlib.suppress(OSError):
                module_with_path.with_suffix('.pyc').unlink()
            with contextlib.suppress(OSError):
                module_with_path.with_suffix('.pyo').unlink()

        def assert_equal(target, value):
            self.assertEqual(target, value)

        class UnicharsSemantics:
            """Check all rule parameters for expected types and values"""

            def rule_positional(self, ast, p1):
                assert_equal('ÄÖÜäöüß', p1)
                return ast

            def rule_keyword(self, ast, k1):
                assert_equal('äöüÄÖÜß', k1)
                return ast

            def rule_all(self, ast, p1, k1):
                assert_equal('ßÄÖÜäöü', p1)
                assert_equal('ßäöüÄÖÜ', k1)
                return ast

        m = compile(grammar, 'UnicodeRuleArguments')
        ast = m.parse('a b c')
        self.assertEqual(['a', 'b', 'c'], ast)

        semantics = UnicharsSemantics()
        ast = m.parse('a b c', semantics=semantics)
        self.assertEqual(['a', 'b', 'c'], ast)

        code = codegen(m)
        import codecs
        module_name = 'tc36unicharstest'
        temp_dir = pathlib.Path(tempfile.mkdtemp()) / module_name
        temp_dir.mkdir(exist_ok=True)
        py_file_path = temp_dir / f'{module_name}.py'

        with codecs.open(py_file_path, 'w', 'utf-8') as f:
            f.write(code)
        try:
            sys.path.append(str(temp_dir))
            import tc36unicharstest  # pylint: disable=E0401

            assert tc36unicharstest
            _trydelete(temp_dir, module_name)
        except Exception as e:
            self.fail(e)

    def test_numbers_and_unicode(self):
        grammar = """
            rúle(1, -23, 4.56, 7.89e-11, Añez)
                =
                'a'
                ;


            rúlé::Añez
                =
                'ñ'
                ;
        """

        model = compile(grammar, 'test')
        self.assertEqual(trim(grammar), str(model))
