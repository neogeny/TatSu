# -*- coding: utf-8 -*-
import unittest

from tatsu.util import trim
from tatsu.tool import compile


class PrettyTests(unittest.TestCase):

    def test_pretty(self):
        grammar = r'''
            start = lisp ;
            lisp = sexp | list | symbol;
            sexp::SExp = '(' cons:lisp '.' ~ cdr:lisp ')' ;
            list::List = '(' elements:{sexp}* ')' ;
            symbol::Symbol = value:/[^\s().]+/ ;
        '''

        pretty = trim(r'''
            start
                =
                lisp
                ;


            lisp
                =
                sexp | list | symbol
                ;


            sexp::SExp
                =
                '(' cons:lisp '.' ~ cdr:lisp ')'
                ;


            list::List
                =
                '(' elements:{sexp} ')'
                ;


            symbol::Symbol
                =
                value:/[^\s().]+/
                ;
        ''')

        pretty_lean = trim(r'''
            start
                =
                lisp
                ;


            lisp
                =
                sexp | list | symbol
                ;


            sexp
                =
                '(' lisp '.' ~ lisp ')'
                ;


            list
                =
                '(' {sexp} ')'
                ;


            symbol
                =
                /[^\s().]+/
                ;
        ''')

        model = compile(grammar=grammar)

        self.assertEqual(pretty, model.pretty())
        self.assertEqual(str(model), model.pretty())

        self.assertEqual(pretty_lean, model.pretty_lean())

    def test_slashed_pattern(self):
        grammar = '''
            start
                =
                ?"[a-z]+/[0-9]+" $
                ;
        '''
        model = compile(grammar=grammar)
        ast = model.parse('abc/123')
        self.assertEqual('abc/123', ast)
        print(model.pretty())
        self.assertEqual(trim(grammar), model.pretty())
